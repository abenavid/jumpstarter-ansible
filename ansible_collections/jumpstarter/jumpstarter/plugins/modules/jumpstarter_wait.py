#!/usr/bin/python

# Copyright: (c) Jumpstarter Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re
import time
from typing import Any

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.jumpstarter.jumpstarter.plugins.module_utils.jumpstarter_common import (  # type: ignore
        run_jmp_shell,
    )
except Exception:  # pragma: no cover
    run_jmp_shell = None  # type: ignore


DOCUMENTATION = r"""
---
module: jumpstarter_wait
short_description: Wait for a device to reach a ready state using retries and backoff
description:
  - Waits for a device to reach a desired state after actions like power cycle.
  - Supports readiness signals such as a serial prompt, a heartbeat file, or a ready command by repeatedly running a check.
  - Implements retries with exponential backoff and returns detailed attempt history.
  - Can run either a generic command (for easy testing) or a Jumpstarter shell command via C(jmp shell).
version_added: "0.1.0"
author:
  - Jumpstarter Contributors
options:
  exporter:
    description:
      - Exporter name.
      - Required when using C(check_shell_cmd).
      - Not required when using C(check_cmd).
    type: str
    required: false
  check_cmd:
    description:
      - A command list to execute repeatedly until success.
      - This runs directly in the execution environment using Ansible's run_command.
      - Use this for generic checks or for unit testing without a real Jumpstarter controller or device.
      - Mutually exclusive with C(check_shell_cmd).
    type: list
    elements: str
    required: false
  check_shell_cmd:
    description:
      - A single command string to execute inside C(jmp shell).
      - Example values:
        - C(j shell ready)
        - C(j shell test -f /tmp/heartbeat && echo READY)
      - Mutually exclusive with C(check_cmd).
    type: str
    required: false
  success_regex:
    description:
      - Optional regex that must match stdout (or stdout plus stderr) for the attempt to be considered successful.
      - If unset, success is based only on return code 0.
    type: str
    required: false
    default: null
  search_stderr:
    description:
      - When true, regex is matched against stdout plus stderr.
      - When false, regex is matched against stdout only.
    type: bool
    required: false
    default: true
  retries:
    description:
      - Number of attempts before failing.
    type: int
    required: false
    default: 10
  delay:
    description:
      - Initial delay in seconds between attempts.
    type: float
    required: false
    default: 2.0
  backoff:
    description:
      - Exponential backoff multiplier applied to delay after each failure.
      - Effective delay is min(delay * backoff^(attempt-1), max_delay).
    type: float
    required: false
    default: 1.5
  max_delay:
    description:
      - Maximum delay in seconds between attempts.
    type: float
    required: false
    default: 30.0
  timeout:
    description:
      - Optional timeout in seconds applied to the underlying check command invocation.
      - Note: some Ansible runtimes do not support passing timeout into run_command, in which case the module will run without a timeout.
      - For C(check_shell_cmd), this is passed through to the Jumpstarter shell helper if supported.
    type: int
    required: false
    default: null
notes:
  - This module does not change device state. It only waits and validates readiness.
  - For heartbeat file checks, prefer a check that returns quickly and reliably (rc 0 when ready).
  - For serial prompt checks, build your check command so it does not block forever. Use a timeout inside the command if needed.
"""

EXAMPLES = r"""
- name: Wait for device to be ready via a shell "ready" command
  jumpstarter.jumpstarter.jumpstarter_wait:
    exporter: test
    check_shell_cmd: "j shell ready"
    retries: 20
    delay: 2
    backoff: 1.4
    success_regex: "READY|ready"

- name: Wait for a heartbeat file on the device using shell driver
  jumpstarter.jumpstarter.jumpstarter_wait:
    exporter: test
    check_shell_cmd: "j shell test -f /var/run/heartbeat && echo READY"
    retries: 30
    delay: 1
    backoff: 1.2
    success_regex: "READY"

- name: Wait using a generic command (great for testing logic without Jumpstarter)
  jumpstarter.jumpstarter.jumpstarter_wait:
    check_cmd: ["bash", "-lc", "test -f /tmp/device_ready"]
    retries: 10
    delay: 1
    backoff: 2.0
"""

RETURN = r"""
ready:
  description: Whether the readiness condition was met within retries.
  type: bool
  returned: always
attempts:
  description: Number of attempts executed.
  type: int
  returned: always
elapsed:
  description: Total elapsed seconds spent waiting.
  type: float
  returned: always
last_rc:
  description: Return code from the last attempt.
  type: int
  returned: always
last_stdout:
  description: Stdout from the last attempt.
  type: str
  returned: always
last_stderr:
  description: Stderr from the last attempt.
  type: str
  returned: always
history:
  description: Attempt history including rc, stdout, stderr, delay used.
  type: list
  elements: dict
  returned: always
"""


def _validate_args(module: AnsibleModule) -> None:
    exporter = module.params.get("exporter")
    check_cmd = module.params.get("check_cmd")
    check_shell_cmd = module.params.get("check_shell_cmd")

    if bool(check_cmd) == bool(check_shell_cmd):
        module.fail_json(
            msg="You must set exactly one of check_cmd or check_shell_cmd (they are mutually exclusive)."
        )

    if check_shell_cmd and not exporter:
        module.fail_json(msg="exporter is required when using check_shell_cmd.")

    if check_shell_cmd and run_jmp_shell is None:
        module.fail_json(
            msg="jumpstarter_common.run_jmp_shell could not be imported. Ensure the collection module_utils is present."
        )


def _compile_regex(pattern: str | None) -> re.Pattern[str] | None:
    if not pattern:
        return None
    return re.compile(pattern)


def _run_command_compatible(module: AnsibleModule, cmd: list[str], timeout: int | None):
    """
    Some Ansible versions do not accept timeout as a keyword argument on run_command.
    We attempt to use it, and fall back cleanly if unsupported.
    """
    if timeout is None:
        return module.run_command(cmd)

    try:
        return module.run_command(cmd, timeout=timeout)  # type: ignore[call-arg]
    except TypeError:
        return module.run_command(cmd)


def _attempt_check(
    module: AnsibleModule,
    exporter: str | None,
    check_cmd: list[str] | None,
    check_shell_cmd: str | None,
    regex: re.Pattern[str] | None,
    search_stderr: bool,
    timeout: int | None,
) -> dict[str, Any]:
    if check_cmd:
        rc, out, err = _run_command_compatible(module, check_cmd, timeout)
        return {"rc": rc, "stdout": out or "", "stderr": err or "", "cmd": check_cmd}

    rc, out, err = run_jmp_shell(  # type: ignore[misc]
        module=module,
        exporter=exporter,
        commands=[check_shell_cmd],
        timeout=timeout,
    )
    return {"rc": rc, "stdout": out or "", "stderr": err or "", "cmd": ["jmp shell", check_shell_cmd]}


def _is_success(
    attempt: dict[str, Any],
    regex: re.Pattern[str] | None,
    search_stderr: bool,
) -> bool:
    if attempt["rc"] != 0:
        return False

    if regex is None:
        return True

    haystack = attempt["stdout"]
    if search_stderr:
        haystack = haystack + "\n" + attempt["stderr"]

    return bool(regex.search(haystack))


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            exporter=dict(type="str", required=False),
            check_cmd=dict(type="list", elements="str", required=False),
            check_shell_cmd=dict(type="str", required=False),
            success_regex=dict(type="str", required=False, default=None),
            search_stderr=dict(type="bool", required=False, default=True),
            retries=dict(type="int", required=False, default=10),
            delay=dict(type="float", required=False, default=2.0),
            backoff=dict(type="float", required=False, default=1.5),
            max_delay=dict(type="float", required=False, default=30.0),
            timeout=dict(type="int", required=False, default=None),
        ),
        supports_check_mode=True,
        mutually_exclusive=[("check_cmd", "check_shell_cmd")],
    )

    _validate_args(module)

    exporter = module.params.get("exporter")
    check_cmd = module.params.get("check_cmd")
    check_shell_cmd = module.params.get("check_shell_cmd")
    regex = _compile_regex(module.params.get("success_regex"))
    search_stderr = module.params.get("search_stderr")
    retries = module.params.get("retries")
    delay = float(module.params.get("delay"))
    backoff = float(module.params.get("backoff"))
    max_delay = float(module.params.get("max_delay"))
    timeout = module.params.get("timeout")

    if retries < 1:
        module.fail_json(msg="retries must be >= 1")
    if delay < 0:
        module.fail_json(msg="delay must be >= 0")
    if backoff < 1.0:
        module.fail_json(msg="backoff must be >= 1.0")
    if max_delay < 0:
        module.fail_json(msg="max_delay must be >= 0")

    start = time.time()
    history: list[dict[str, Any]] = []

    current_delay = delay
    last_attempt: dict[str, Any] = {"rc": 1, "stdout": "", "stderr": "", "cmd": []}

    for i in range(1, retries + 1):
        attempt = _attempt_check(
            module=module,
            exporter=exporter,
            check_cmd=check_cmd,
            check_shell_cmd=check_shell_cmd,
            regex=regex,
            search_stderr=search_stderr,
            timeout=timeout,
        )
        last_attempt = attempt

        ok = _is_success(attempt, regex, search_stderr)
        history.append(
            {
                "attempt": i,
                "ok": ok,
                "rc": attempt["rc"],
                "stdout": attempt["stdout"],
                "stderr": attempt["stderr"],
                "cmd": attempt["cmd"],
                "sleep": 0.0 if ok or i == retries else min(current_delay, max_delay),
            }
        )

        if ok:
            elapsed = time.time() - start
            module.exit_json(
                changed=False,
                ready=True,
                attempts=i,
                elapsed=elapsed,
                last_rc=attempt["rc"],
                last_stdout=attempt["stdout"],
                last_stderr=attempt["stderr"],
                history=history,
            )

        if i < retries:
            sleep_for = min(current_delay, max_delay)
            if sleep_for > 0:
                time.sleep(sleep_for)
            current_delay = current_delay * backoff

    elapsed = time.time() - start
    module.fail_json(
        msg="timed out waiting for ready condition",
        changed=False,
        ready=False,
        attempts=retries,
        elapsed=elapsed,
        last_rc=last_attempt["rc"],
        last_stdout=last_attempt["stdout"],
        last_stderr=last_attempt["stderr"],
        history=history,
    )


if __name__ == "__main__":
    main()
