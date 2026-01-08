#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: hatci_deploy_event
short_description: Schedule and trigger an update deployment for a fixed event
version_added: "1.0.0"
description:
  - Schedules and triggers an OTA update deployment based on a fixed event.
  - The event must be fixed (locked) before it can be deployed.

options:
  hatci_base_url:
    description:
      - Base URL for HATCI API
    type: str
    required: true
  hatci_token:
    description:
      - Authentication token for HATCI API
    type: str
    required: true
  verify_tls:
    description:
      - Whether to verify TLS certificates
    type: bool
    default: true
  timeout:
    description:
      - Request timeout in seconds
    type: int
    default: 30
  event_id:
    description:
      - ID of the fixed event to deploy
    type: str
    required: true
  start_datetime:
    description:
      - Start datetime for the deployment window (ISO 8601 format)
    type: str
    required: false
  end_datetime:
    description:
      - End datetime for the deployment window (ISO 8601 format)
    type: str
    required: false
  deployment_count:
    description:
      - Number of deployments to schedule
    type: int
    required: false
    default: 1

author:
  - HATCI Contributors
"""

RETURN = r"""
deployment_id:
  description: Unique identifier for the created deployment
  returned: always
  type: str
state:
  description: Current state of the deployment
  returned: always
  type: str
deployment:
  description: Full deployment object
  returned: always
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.hatci.automation.plugins.module_utils.hatci_client import (
        HATCIClient,
        HATCIClientError,
    )
except ImportError:
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from module_utils.hatci_client import HATCIClient, HATCIClientError


def main():
    argument_spec = dict(
        hatci_base_url=dict(type="str", required=True),
        hatci_token=dict(type="str", required=True, no_log=True),
        verify_tls=dict(type="bool", default=True),
        timeout=dict(type="int", default=30),
        event_id=dict(type="str", required=True),
        start_datetime=dict(type="str", required=False),
        end_datetime=dict(type="str", required=False),
        deployment_count=dict(type="int", required=False, default=1),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    # Build deployment payload
    payload = {
        "event_id": module.params["event_id"],
        "deployment_count": module.params.get("deployment_count", 1),
    }

    if module.params.get("start_datetime"):
        payload["start_datetime"] = module.params["start_datetime"]
    if module.params.get("end_datetime"):
        payload["end_datetime"] = module.params["end_datetime"]

    try:
        client = HATCIClient(
            base_url=module.params["hatci_base_url"],
            token=module.params["hatci_token"],
            verify_tls=module.params["verify_tls"],
            timeout=module.params["timeout"],
        )

        response = client.post("/api/v1/deployments", data=payload)

        deployment_id = response.get("deployment_id") or response.get("id")
        state = response.get("state", "PENDING")

        if not deployment_id:
            module.fail_json(msg="API response missing deployment_id", response=response)

        module.exit_json(
            changed=True,
            deployment_id=deployment_id,
            state=state,
            deployment=response,
        )

    except HATCIClientError as e:
        module.fail_json(msg=str(e), changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}", changed=False)


if __name__ == "__main__":
    main()
