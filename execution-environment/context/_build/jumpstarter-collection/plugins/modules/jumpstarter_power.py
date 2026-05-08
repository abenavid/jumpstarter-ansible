#!/usr/bin/python

from __future__ import annotations

DOCUMENTATION = r"""
---
module: jumpstarter_power
short_description: Control device power via Jumpstarter
version_added: "0.1.0"
description:
  - Control device power using the Jumpstarter C(j power) commands executed
    through C(jmp shell --exporter <name>).
  - This module provides a more Ansible-friendly interface around common
    power operations (on, off, cycle).
options:
  exporter:
    description:
      - Name of the Jumpstarter exporter to use.
      - Must correspond to a YAML exporter configuration available to
        Jumpstarter (for example, in C(/etc/jumpstarter/exporters)).
      - The exporter must define an C(export.power) driver; otherwise
        C(j power ...) commands issued by this module will fail.
    type: str
    required: true
  state:
    description:
      - Desired power state of the device.
    type: str
    required: true
    choices:
      - on
      - off
      - cycle
  wait:
    description:
      - Number of seconds to wait after the power operation, passed as
        C(--wait) to C(j power).
    type: int
    required: false
  timeout:
    description:
      - Timeout in seconds for the underlying C(jmp shell) process.
    type: int
    required: false
  check_rc:
    description:
      - If C(true), fail the task when the return code of C(jmp shell)
        is non-zero.
    type: bool
    default: true
author:
  - Alex Benavides <abenavid@redhat.com>
"""

EXAMPLES = r"""
- name: Cycle power with a 1 second wait
  jumpstarter_power:
    exporter: test
    state: cycle
    wait: 1

- name: Turn device power on
  jumpstarter_power:
    exporter: test
    state: on
"""

RETURN = r"""
rc:
  description: Return code from the C(jmp shell) process.
  type: int
  returned: always
stdout:
  description: Standard output from C(jmp shell).
  type: str
  returned: always
stderr:
  description: Standard error from C(jmp shell).
  type: str
  returned: always
cmd:
  description: The C(jmp shell) command that was executed.
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.jumpstarter.jumpstarter.plugins.module_utils.jumpstarter_common import (  # type: ignore[attr-defined]  # noqa: E501
    run_jmp_shell,
)


def build_power_command(state: str, wait: int | None) -> str:
    parts = ["j", "power", state]
    if wait is not None:
        parts.extend(["--wait", str(wait)])
    return " ".join(parts)


def run_module() -> None:
    module_args = dict(
        exporter=dict(type="str", required=True),
        state=dict(type="str", required=True, choices=["on", "off", "cycle"]),
        wait=dict(type="int", required=False),
        timeout=dict(type="int", required=False),
        check_rc=dict(type="bool", required=False, default=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    exporter = module.params["exporter"]
    state = module.params["state"]
    wait = module.params.get("wait")
    timeout = module.params.get("timeout")
    check_rc = module.params.get("check_rc")

    cmd_str = build_power_command(state=state, wait=wait)

    if module.check_mode:
        module.exit_json(
            changed=True,
            rc=0,
            stdout="",
            stderr="",
            cmd=f"jmp shell --exporter {exporter}",
            j_command=cmd_str,
        )

    try:
        rc, stdout, stderr, cmd = run_jmp_shell(
            exporter=exporter,
            commands=[cmd_str],
            timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - defensive
        module.fail_json(msg=str(exc))

    if check_rc and rc != 0:
        module.fail_json(
            msg="jmp shell returned non-zero exit status",
            rc=rc,
            stdout=stdout,
            stderr=stderr,
            cmd=cmd,
            j_command=cmd_str,
        )

    module.exit_json(
        changed=True,
        rc=rc,
        stdout=stdout,
        stderr=stderr,
        cmd=cmd,
        j_command=cmd_str,
    )


def main() -> None:
    run_module()


if __name__ == "__main__":
    main()


