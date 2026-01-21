#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: hatci_update_status
short_description: Poll the backend for the status of a deployment or event
version_added: "1.0.0"
description:
  - Retrieves the current status of a deployment or event from the HATCI API.
  - Can be used to poll for status updates during OTA operations.

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
  deployment_id:
    description:
      - ID of the deployment to check (mutually exclusive with event_id)
    type: str
    required: false
  event_id:
    description:
      - ID of the event to check (mutually exclusive with deployment_id)
    type: str
    required: false

author:
  - Alex Benavides <abenavid@redhat.com>

notes:
  - Either deployment_id or event_id must be provided, but not both.
"""

RETURN = r"""
state:
  description: Current state (PENDING, IN_PROGRESS, COMPLETE, FAILED, etc.)
  returned: always
  type: str
reason:
  description: Reason for failure, if state is FAILED
  returned: when state is FAILED
  type: str
timestamps:
  description: Dictionary of relevant timestamps
  returned: always
  type: dict
status:
  description: Full status object from API
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
        deployment_id=dict(type="str", required=False),
        event_id=dict(type="str", required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=[("deployment_id", "event_id")],
        required_one_of=[("deployment_id", "event_id")],
    )

    deployment_id = module.params.get("deployment_id")
    event_id = module.params.get("event_id")

    try:
        client = HATCIClient(
            base_url=module.params["hatci_base_url"],
            token=module.params["hatci_token"],
            verify_tls=module.params["verify_tls"],
            timeout=module.params["timeout"],
        )

        # Determine which endpoint to use
        if deployment_id:
            response = client.get(f"/api/v1/deployments/{deployment_id}")
        else:
            response = client.get(f"/api/v1/events/{event_id}")

        state = response.get("state", response.get("status", "UNKNOWN"))
        reason = response.get("reason") or response.get("error_message")
        timestamps = response.get("timestamps", {})

        result = {
            "changed": False,
            "state": state,
            "timestamps": timestamps,
            "status": response,
        }

        if reason:
            result["reason"] = reason

        module.exit_json(**result)

    except HATCIClientError as e:
        module.fail_json(msg=str(e), changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}", changed=False)


if __name__ == "__main__":
    main()
