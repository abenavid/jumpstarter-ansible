#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Jumpstarter Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: jumpstarter_preflight
short_description: Preflight checks for Jumpstarter execution environment and optional exporter validation
description:
  - Verifies that C(jmp) is available in PATH and returns its version.
  - Optionally verifies Jumpstarter config directories exist.
  - Optionally verifies a named exporter exists in Jumpstarter inventory.
  - Designed to run early in a play as a safety gate before any device operations.
version_added: "0.1.0"
author:
  - Alex Benavides <abenavid@redhat.com>
options:
  exporter:
    description:
      - Exporter name to validate is available to Jumpstarter.
      - If provided and C(fail_on_missing_exporter) is true, the module fails when the exporter is not found.
      - Exporter validation requires exporter discovery unless C(skip_exporter_query) is true.
    type: str
    required: false

  fail_on_missing_exporter:
    description:
      - When true, fail the task if C(exporter) is set and the exporter is not found.
    type: bool
    default: true

  check_config_dirs:
    description:
      - When true, report whether config directories exist inside the container.
      - Jumpstarter commonly uses a user config directory and an exporter config directory.
    type: bool
    default: true

  user_config_dir:
    description:
      - Path to Jumpstarter user config directory (default aligns with Jumpstarter docs).
    type: str
    default: "~/.config/jumpstarter"

  exporters_dir:
    description:
      - Path to exporter configuration directory.
    type: str
    default: "/etc/jumpstarter/exporters"

  client_config:
    description:
      - Path to a Jumpstarter client config file inside the execution environment.
      - When provided, exporter discovery will include C(--client-config <path>) on the C(jmp get exporters) subcommand.
      - Recommended for AAP and CI where you mount a config file into the container.
    type: str
    required: false

  client:
    description:
      - Named Jumpstarter client alias to use for exporter discovery.
      - When provided, exporter discovery will include C(--client <name>) on the C(jmp get exporters) subcommand.
    type: str
    required: false

  skip_exporter_query:
    description:
      - When true, do not run C(jmp get exporters -o json).
      - Use this for smoke testing that only validates C(jmp) exists and returns a version.
      - If true and C(exporter) is set, exporter validation cannot be performed.
    type: bool
    default: false

  timeout:
    description:
      - Timeout in seconds for underlying C(jmp) commands.
    type: int
    required: false

notes:
  - Exporter discovery requires Jumpstarter client context. If you do not provide C(client_config) or C(client),
    Jumpstarter may rely on a default config under the user config directory.
  - If Jumpstarter returns an error indicating no client context, provide C(client_config) or C(client).
"""

EXAMPLES = r"""
- name: Preflight check before any device actions (requires Jumpstarter default client config)
  jumpstarter.jumpstarter.jumpstarter_preflight:
    exporter: test

- name: Preflight check using a mounted client config file
  jumpstarter.jumpstarter.jumpstarter_preflight:
    exporter: test
    client_config: /etc/jumpstarter/client.yaml

- name: Smoke test only, do not validate exporter inventory or directories
  jumpstarter.jumpstarter.jumpstarter_preflight:
    skip_exporter_query: true
    check_config_dirs: false
    fail_on_missing_exporter: false
"""

RETURN = r"""
cmds:
  description: Commands executed during preflight.
  returned: always
  type: list
  elements: str

jmp_present:
  description: Whether C(jmp) was found and executed.
  returned: always
  type: bool

jmp_version:
  description: Output of C(jmp version) when available.
  returned: always
  type: str

user_config_dir:
  description: Resolved user config directory path.
  returned: always
  type: str

user_config_dir_exists:
  description: Whether user config directory exists.
  returned: always
  type: bool

exporters_dir:
  description: Exporters directory path.
  returned: always
  type: str

exporters_dir_exists:
  description: Whether exporters directory exists.
  returned: always
  type: bool

exporters:
  description: Exporter names discovered via C(jmp get exporters -o json), when available.
  returned: always
  type: list
  elements: str

exporter:
  description: Exporter name requested for validation.
  returned: when exporter is provided
  type: str

exporter_present:
  description: Whether requested exporter exists in discovered exporter list.
  returned: when exporter is provided
  type: bool

error:
  description: Error details when exporter discovery fails.
  returned: when exporter discovery fails
  type: str
"""

import json
import os
import shutil
import subprocess
from typing import List, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule


def _run_cmd(cmd: List[str], timeout: Optional[int]) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ""
        err = e.stderr or ""
        if timeout is not None:
            err = (err + "\n" if err else "") + f"timeout after {timeout}s"
        return 124, out, err
    except FileNotFoundError as e:
        return 127, "", str(e)
    except Exception as e:
        return 1, "", str(e)


def _subcommand_client_args(client: Optional[str], client_config: Optional[str]) -> List[str]:
    """
    Jumpstarter's --client/--client-config flags are typically options on subcommands
    like `jmp get exporters`, not global options on `jmp`.
    Preference: client_config over client when both are provided.
    """
    if client_config:
        return ["--client-config", client_config]
    if client:
        return ["--client", client]
    return []


def _cmd_to_str(cmd: List[str]) -> str:
    return " ".join(cmd)


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            exporter=dict(type="str", required=False, default=None),
            fail_on_missing_exporter=dict(type="bool", required=False, default=True),
            check_config_dirs=dict(type="bool", required=False, default=True),
            user_config_dir=dict(type="str", required=False, default="~/.config/jumpstarter"),
            exporters_dir=dict(type="str", required=False, default="/etc/jumpstarter/exporters"),
            client_config=dict(type="str", required=False, default=None),
            client=dict(type="str", required=False, default=None),
            skip_exporter_query=dict(type="bool", required=False, default=False),
            timeout=dict(type="int", required=False, default=None),
        ),
        supports_check_mode=True,
    )

    exporter: Optional[str] = module.params.get("exporter")
    fail_on_missing_exporter: bool = module.params["fail_on_missing_exporter"]
    check_config_dirs: bool = module.params["check_config_dirs"]
    user_config_dir_raw: str = module.params["user_config_dir"]
    exporters_dir: str = module.params["exporters_dir"]
    client_config: Optional[str] = module.params.get("client_config")
    client: Optional[str] = module.params.get("client")
    skip_exporter_query: bool = module.params["skip_exporter_query"]
    timeout: Optional[int] = module.params.get("timeout")

    cmds: List[str] = []

    user_config_dir = os.path.expanduser(user_config_dir_raw)

    exporters_dir_exists = os.path.isdir(exporters_dir)
    user_config_dir_exists = os.path.isdir(user_config_dir)

    jmp_path = shutil.which("jmp")
    if not jmp_path:
        module.fail_json(
            msg="jmp not found in PATH",
            cmds=cmds,
            jmp_present=False,
            jmp_version="",
            exporters=[],
            exporters_dir=exporters_dir,
            exporters_dir_exists=exporters_dir_exists,
            user_config_dir=user_config_dir,
            user_config_dir_exists=user_config_dir_exists,
        )

    rc_v, out_v, err_v = _run_cmd(["jmp", "version"], timeout=timeout)
    cmds.append("jmp version")
    if rc_v != 0:
        module.fail_json(
            msg="failed to execute jmp version",
            cmds=cmds,
            jmp_present=True,
            jmp_version=out_v.strip(),
            error=err_v.strip(),
            exporters=[],
            exporters_dir=exporters_dir,
            exporters_dir_exists=exporters_dir_exists,
            user_config_dir=user_config_dir,
            user_config_dir_exists=user_config_dir_exists,
        )

    exporters: List[str] = []
    exporter_present: Optional[bool] = None

    if exporter and skip_exporter_query and fail_on_missing_exporter:
        module.fail_json(
            msg="cannot validate exporter when skip_exporter_query is true; set skip_exporter_query false or fail_on_missing_exporter false",
            cmds=cmds,
            jmp_present=True,
            jmp_version=out_v.strip(),
            exporter=exporter,
            exporter_present=False,
            exporters=[],
            exporters_dir=exporters_dir,
            exporters_dir_exists=exporters_dir_exists,
            user_config_dir=user_config_dir,
            user_config_dir_exists=user_config_dir_exists,
        )

    if not skip_exporter_query:
        # Build as: jmp get exporters [--client-config/--client] -o json
        cmd_list: List[str] = ["jmp", "get", "exporters"]
        cmd_list += _subcommand_client_args(client=client, client_config=client_config)
        cmd_list += ["-o", "json"]

        cmds.append(_cmd_to_str(cmd_list))

        rc_e, out_e, err_e = _run_cmd(cmd_list, timeout=timeout)
        if rc_e != 0:
            msg = "failed to query exporters from jumpstarter"
            lowered = (err_e or "").lower()
            if "none of --client" in lowered or "default config is not set" in lowered:
                msg = "jumpstarter client context is not configured; provide client_config or client, or configure a default client in the container"
            module.fail_json(
                msg=msg,
                cmds=cmds,
                jmp_present=True,
                jmp_version=out_v.strip(),
                error=err_e.strip(),
                exporter=exporter,
                exporter_present=False if exporter else None,
                exporters=[],
                exporters_dir=exporters_dir,
                exporters_dir_exists=exporters_dir_exists,
                user_config_dir=user_config_dir,
                user_config_dir_exists=user_config_dir_exists,
            )

        try:
            data = json.loads(out_e) if out_e.strip() else []
        except Exception as e:
            module.fail_json(
                msg="failed to parse exporters json output",
                cmds=cmds,
                jmp_present=True,
                jmp_version=out_v.strip(),
                error=str(e),
                exporter=exporter,
                exporter_present=False if exporter else None,
                exporters=[],
                exporters_dir=exporters_dir,
                exporters_dir_exists=exporters_dir_exists,
                user_config_dir=user_config_dir,
                user_config_dir_exists=user_config_dir_exists,
            )

        names: List[str] = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
                    names.append(item["name"])
                elif isinstance(item, str):
                    names.append(item)
        elif isinstance(data, dict):
            for k in ("exporters", "items", "results"):
                v = data.get(k)
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
                            names.append(item["name"])
                        elif isinstance(item, str):
                            names.append(item)

        exporters = sorted(set(names))

        if exporter:
            exporter_present = exporter in exporters
            if fail_on_missing_exporter and not exporter_present:
                module.fail_json(
                    msg="exporter not found in jumpstarter inventory",
                    cmds=cmds,
                    jmp_present=True,
                    jmp_version=out_v.strip(),
                    exporter=exporter,
                    exporter_present=False,
                    exporters=exporters,
                    exporters_dir=exporters_dir,
                    exporters_dir_exists=exporters_dir_exists,
                    user_config_dir=user_config_dir,
                    user_config_dir_exists=user_config_dir_exists,
                )

    result = dict(
        changed=False,
        cmds=cmds,
        jmp_present=True,
        jmp_version=out_v.strip(),
        exporters=exporters,
        exporters_dir=exporters_dir,
        exporters_dir_exists=exporters_dir_exists,
        user_config_dir=user_config_dir,
        user_config_dir_exists=user_config_dir_exists,
    )

    if exporter is not None:
        result["exporter"] = exporter
        result["exporter_present"] = bool(exporter_present) if exporter_present is not None else False

    module.exit_json(**result)


if __name__ == "__main__":
    main()
