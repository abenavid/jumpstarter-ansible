#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: hatci_test_event
short_description: Create a record of a test run linking vehicle, event, and Ansible job
version_added: "1.0.0"
description:
  - Creates a test event record in HATCI that links together vehicle information,
    event IDs, and Ansible job metadata.
  - This is used to track test runs and their outcomes.

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
  vin:
    description:
      - Vehicle Identification Number
    type: str
    required: true
  vehicle_id:
    description:
      - Optional vehicle ID if already known
    type: str
    required: false
  event_id:
    description:
      - ID of the event being tested
    type: str
    required: true
  ansible_job_id:
    description:
      - Ansible Automation Platform job ID
    type: str
    required: true
  git_sha:
    description:
      - Git commit SHA of the code being tested
    type: str
    required: true
  suite_name:
    description:
      - Name of the test suite
    type: str
    required: true
  metadata:
    description:
      - Additional metadata dictionary
    type: dict
    required: false

author:
  - HATCI Contributors
"""

RETURN = r"""
test_event_id:
  description: Unique identifier for the created test event
  returned: always
  type: str
test_event:
  description: Full test event object
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
        vin=dict(type="str", required=True),
        vehicle_id=dict(type="str", required=False),
        event_id=dict(type="str", required=True),
        ansible_job_id=dict(type="str", required=True),
        git_sha=dict(type="str", required=True),
        suite_name=dict(type="str", required=True),
        metadata=dict(type="dict", required=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    # Build payload
    payload = {
        "vin": module.params["vin"],
        "event_id": module.params["event_id"],
        "ansible_job_id": module.params["ansible_job_id"],
        "git_sha": module.params["git_sha"],
        "suite_name": module.params["suite_name"],
    }

    if module.params.get("vehicle_id"):
        payload["vehicle_id"] = module.params["vehicle_id"]
    if module.params.get("metadata"):
        payload["metadata"] = module.params["metadata"]

    try:
        client = HATCIClient(
            base_url=module.params["hatci_base_url"],
            token=module.params["hatci_token"],
            verify_tls=module.params["verify_tls"],
            timeout=module.params["timeout"],
        )

        response = client.post("/api/v1/test_events", data=payload)

        test_event_id = response.get("test_event_id") or response.get("id")
        if not test_event_id:
            module.fail_json(msg="API response missing test_event_id", response=response)

        module.exit_json(
            changed=True,
            test_event_id=test_event_id,
            test_event=response,
        )

    except HATCIClientError as e:
        module.fail_json(msg=str(e), changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}", changed=False)


if __name__ == "__main__":
    main()
