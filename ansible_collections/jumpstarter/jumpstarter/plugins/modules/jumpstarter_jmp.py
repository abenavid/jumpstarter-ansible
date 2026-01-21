#!/usr/bin/python

from __future__ import annotations

DOCUMENTATION = r"""
---
module: jumpstarter_jmp
short_description: Run generic Jumpstarter jmp CLI commands
version_added: "0.1.0"
description:
  - Run arbitrary C(jmp) CLI subcommands from Ansible, as described in the
    Jumpstarter C(jmp) man page.
  - This is a low-level escape hatch that lets you drive commands such as
    C(jmp get exporters), C(jmp get leases), C(jmp create lease),
    C(jmp delete leases), C(jmp update lease), C(jmp version), and more.
  - For device-level operations through exporters (for example, C(j power ...)),
    prefer using C(jumpstarter_shell) or higher-level modules such as
    C(jumpstarter_power).
options:
  args:
    description:
      - List of arguments to pass to the C(jmp) CLI, excluding the leading
        C(jmp) itself.
      - The first element is typically a subcommand such as C(get),
        C(create), C(delete), C(update), C(driver), C(version), etc.
    type: list
    elements: str
    required: true
  timeout:
    description:
      - Timeout in seconds for the underlying C(jmp) process.
    type: int
    required: false
  check_rc:
    description:
      - If C(true), fail the task when the return code of C(jmp) is non-zero.
    type: bool
    default: true
author:
  - Alex Benavides <abenavid@redhat.com>
"""

EXAMPLES = r"""
- name: Get exporters as JSON
  jumpstarter_jmp:
    args:
      - get
      - exporters
      - -o
      - json
  register: exporters_info

- name: Get all leases including expired ones
  jumpstarter_jmp:
    args:
      - get
      - leases
      - --all
      - -o
      - json

- name: Show Jumpstarter driver version
  jumpstarter_jmp:
    args:
      - driver
      - version
      - -o
      - json

- name: Show Jumpstarter service version
  jumpstarter_jmp:
    args:
      - version
      - -o
      - json
"""

RETURN = r"""
rc:
  description: Return code from the C(jmp) process.
  type: int
  returned: always
stdout:
  description: Standard output from C(jmp).
  type: str
  returned: always
stderr:
  description: Standard error from C(jmp).
  type: str
  returned: always
cmd:
  description: The full C(jmp) command that was executed.
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.jumpstarter.jumpstarter.plugins.module_utils.jumpstarter_common import (  # type: ignore[attr-defined]  # noqa: E501
    run_jmp,
)


def run_module() -> None:
    module_args = dict(
        args=dict(type="list", elements="str", required=True),
        timeout=dict(type="int", required=False),
        check_rc=dict(type="bool", required=False, default=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    args = module.params["args"]
    timeout = module.params.get("timeout")
    check_rc = module.params.get("check_rc")

    if not args:
        module.fail_json(msg="parameter 'args' must be a non-empty list")

    if module.check_mode:
        module.exit_json(
            changed=False,
            rc=0,
            stdout="",
            stderr="",
            cmd="jmp " + " ".join(args),
        )

    try:
        rc, stdout, stderr, cmd = run_jmp(
            args=args,
            timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - defensive
        module.fail_json(msg=str(exc))

    if check_rc and rc != 0:
        module.fail_json(
            msg="jmp returned non-zero exit status",
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


