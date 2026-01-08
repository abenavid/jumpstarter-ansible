#!/usr/bin/python

from __future__ import annotations

DOCUMENTATION = r"""
---
module: jumpstarter_shell
short_description: Run Jumpstarter j commands via jmp shell
version_added: "0.1.0"
description:
  - Run one or more Jumpstarter C(j) commands through
    C(jmp shell --exporter <name>) and capture the output.
  - This module is a thin wrapper over the Jumpstarter CLI and assumes
    that C(jmp) is available in PATH inside the Ansible execution
    environment.
options:
  exporter:
    description:
      - Name of the Jumpstarter exporter to use.
      - Must correspond to a YAML file in
        C(/etc/jumpstarter/exporters/<exporter>.yaml) or another location
        configured for Jumpstarter.
      - The exporter configuration determines which drivers (power, storage,
        serial, etc.) are available; only commands supported by those drivers
        will succeed.
    type: str
    required: true
  command:
    description:
      - Single C(j) command to run inside the Jumpstarter shell.
      - Mutually exclusive with I(commands).
    type: str
  commands:
    description:
      - List of C(j) commands to run in order inside the Jumpstarter
        shell.
      - Mutually exclusive with I(command).
    type: list
    elements: str
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
  - Jumpstarter Contributors
"""

EXAMPLES = r"""
- name: Run a single Jumpstarter power command
  jumpstarter_shell:
    exporter: test
    command: "j power cycle --wait 1"

- name: Run multiple Jumpstarter commands in sequence
  jumpstarter_shell:
    exporter: test
    commands:
      - "j power off"
      - "j power on --wait 2"
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


def run_module() -> None:
    module_args = dict(
        exporter=dict(type="str", required=True),
        command=dict(type="str", required=False),
        commands=dict(type="list", elements="str", required=False),
        timeout=dict(type="int", required=False),
        check_rc=dict(type="bool", required=False, default=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[["command", "commands"]],
    )

    exporter = module.params["exporter"]
    command = module.params.get("command")
    commands = module.params.get("commands")
    timeout = module.params.get("timeout")
    check_rc = module.params.get("check_rc")

    if not command and not commands:
        module.fail_json(msg="either 'command' or 'commands' must be provided")

    if command and commands:
        module.fail_json(msg="only one of 'command' or 'commands' may be provided")

    if command:
        cmd_list = [command]
    else:
        cmd_list = commands or []

    if module.check_mode:
        module.exit_json(
            changed=False,
            rc=0,
            stdout="",
            stderr="",
            cmd=f"jmp shell --exporter {exporter}",
        )

    try:
        rc, stdout, stderr, cmd = run_jmp_shell(
            exporter=exporter,
            commands=cmd_list,
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
        )

    module.exit_json(
        changed=True,
        rc=rc,
        stdout=stdout,
        stderr=stderr,
        cmd=cmd,
    )


def main() -> None:
    run_module()


if __name__ == "__main__":
    main()


