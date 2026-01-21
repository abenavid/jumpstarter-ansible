#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) Jumpstarter Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: jumpstarter_lease
short_description: Manage Jumpstarter device leases using the jmp CLI
version_added: "0.1.0"
description:
  - Creates, renews, and releases Jumpstarter leases so users do not have to hand roll lease flows.
  - Uses the C(jmp) CLI inside the execution environment.
  - Supports optional Jumpstarter client context via C(client_config) or C(client).

options:
  state:
    description:
      - Operation to perform.
      - Note: C(action) is a deprecated alias because "action" is a reserved Ansible task keyword.
    type: str
    required: true
    choices:
      - acquire
      - create
      - renew
      - release

  selector:
    description:
      - Selector for lease creation, typically includes exporter matching.
      - Example: C(exporter=test)
      - Required for C(create) and C(acquire).
    type: str
    required: false

  duration:
    description:
      - Lease duration passed to C(jmp create lease --duration ...).
      - Examples: C(30m), C(3h30m), C(1d), or C(00:30:00) depending on CLI support.
      - Required for C(create) and C(acquire).
    type: str
    required: false

  lease_name:
    description:
      - Name of an existing lease to renew or release.
      - Required for C(renew) and C(release).
    type: str
    required: false

  output:
    description:
      - Output format for lease creation.
      - C(name) is the most convenient for automation.
    type: str
    required: false
    default: name
    choices:
      - name
      - json

  client_config:
    description:
      - Path inside the execution environment to a Jumpstarter client config file.
      - When set, commands include C(--client-config <path>) in the correct position.
    type: str
    required: false

  client:
    description:
      - Named Jumpstarter client to use.
      - When set, commands include C(--client <name>) in the correct position.
    type: str
    required: false

  timeout:
    description:
      - Best effort timeout in seconds for command execution.
      - This module does not rely on AnsibleModule.run_command(timeout=...) because that parameter
        is not available in all Ansible versions. Timeout is currently informational only.
    type: int
    required: false

author:
  - Alex Benavides <abenavid@redhat.com>

notes:
  - This module shells out to C(jmp). Ensure the CLI is installed in the execution environment.
  - For AAP and CI, prefer mounting a client config file and referencing it with C(client_config).

examples:
  - name: Acquire a lease for exporter "test" for 30 minutes
    jumpstarter.jumpstarter.jumpstarter_lease:
      state: acquire
      selector: "exporter=test"
      duration: "30m"
      output: name

  - name: Release a lease by name
    jumpstarter.jumpstarter.jumpstarter_lease:
      state: release
      lease_name: "lease/test-123"

  - name: Acquire using a mounted client config
    jumpstarter.jumpstarter.jumpstarter_lease:
      state: acquire
      selector: "exporter=test"
      duration: "30m"
      client_config: "/private/etc/jumpstarter/client.yaml"
"""

RETURN = r"""
lease_name:
  description: Lease name returned from create or acquire.
  returned: when state is create or acquire
  type: str
cmds:
  description: Commands executed.
  returned: always
  type: list
  elements: str
rc:
  description: Return code from the last jmp command.
  returned: on failure
  type: int
raw_stdout:
  description: Raw stdout from the last jmp command.
  returned: on failure
  type: str
raw_stderr:
  description: Raw stderr from the last jmp command.
  returned: on failure
  type: str
"""

from ansible.module_utils.basic import AnsibleModule


def _client_args(module: AnsibleModule) -> list[str]:
    # For this module, the CLI shape that worked in your preflight is:
    #   jmp get exporters --client-config <path> -o json
    # For lease operations we keep the same approach: put client args after the subcommand.
    args: list[str] = []
    client_config = module.params.get("client_config")
    client = module.params.get("client")

    if client_config and client:
        module.fail_json(msg="Provide only one of client_config or client, not both.")

    if client_config:
        args.extend(["--client-config", client_config])
    elif client:
        args.extend(["--client", client])

    return args


def _run(module: AnsibleModule, cmd: list[str], cmds_log: list[str]) -> tuple[int, str, str]:
    cmds_log.append(" ".join(cmd))
    rc, out, err = module.run_command(cmd)
    return rc, out or "", err or ""


def main() -> None:
    argument_spec = dict(
        # IMPORTANT: use "state" as the real argument name
        # and allow "action" only as an alias.
        state=dict(type="str", required=True, choices=["acquire", "create", "renew", "release"], aliases=["action"]),
        selector=dict(type="str", required=False),
        duration=dict(type="str", required=False),
        lease_name=dict(type="str", required=False),
        output=dict(type="str", required=False, default="name", choices=["name", "json"]),
        client_config=dict(type="str", required=False),
        client=dict(type="str", required=False),
        timeout=dict(type="int", required=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    state = module.params["state"]
    selector = module.params.get("selector")
    duration = module.params.get("duration")
    lease_name = module.params.get("lease_name")
    output = module.params.get("output")

    cmds_log: list[str] = []

    # Minimal presence check: jmp version
    rc, out, err = _run(module, ["jmp", "version"], cmds_log)
    if rc != 0:
        module.fail_json(
            msg="jmp is not available or failed to run",
            cmds=cmds_log,
            rc=rc,
            raw_stdout=out,
            raw_stderr=err,
            changed=False,
        )

    client_args = _client_args(module)

    if state in ("create", "acquire"):
        if not selector:
            module.fail_json(msg="selector is required for state=create/acquire", cmds=cmds_log, changed=False)
        if not duration:
            module.fail_json(msg="duration is required for state=create/acquire", cmds=cmds_log, changed=False)

        # jmp create lease -l <selector> --duration <duration> -o <output>
        cmd = ["jmp", "create", "lease", "-l", selector, "--duration", duration, "-o", output]
        # If client args are needed for your environment, append them after the subcommand.
        # Fake jmp ignores them anyway.
        cmd.extend(client_args)

        rc, out, err = _run(module, cmd, cmds_log)
        if rc != 0:
            module.fail_json(
                msg="failed to create lease",
                cmds=cmds_log,
                rc=rc,
                raw_stdout=out,
                raw_stderr=err,
                error=(err.strip() or out.strip()),
                changed=False,
            )

        lease = out.strip()
        module.exit_json(changed=True, lease_name=lease, cmds=cmds_log)

    if state == "renew":
        if not lease_name:
            module.fail_json(msg="lease_name is required for state=renew", cmds=cmds_log, changed=False)

        # Real CLI may support "jmp renew lease <name>" or similar.
        # Keep this as a placeholder until we confirm the exact command from your jmp version.
        cmd = ["jmp", "renew", "lease", lease_name]
        cmd.extend(client_args)

        rc, out, err = _run(module, cmd, cmds_log)
        if rc != 0:
            module.fail_json(
                msg="failed to renew lease",
                cmds=cmds_log,
                rc=rc,
                raw_stdout=out,
                raw_stderr=err,
                error=(err.strip() or out.strip()),
                changed=False,
            )
        module.exit_json(changed=True, cmds=cmds_log)

    if state == "release":
        if not lease_name:
            module.fail_json(msg="lease_name is required for state=release", cmds=cmds_log, changed=False)

        # jmp delete leases <name>
        cmd = ["jmp", "delete", "leases", lease_name]
        cmd.extend(client_args)

        rc, out, err = _run(module, cmd, cmds_log)
        if rc != 0:
            module.fail_json(
                msg="failed to release lease",
                cmds=cmds_log,
                rc=rc,
                raw_stdout=out,
                raw_stderr=err,
                error=(err.strip() or out.strip()),
                changed=False,
            )
        module.exit_json(changed=True, cmds=cmds_log)

    module.fail_json(msg=f"unsupported state: {state}", cmds=cmds_log, changed=False)


if __name__ == "__main__":
    main()
