#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: hatci_test_event_update
short_description: Update a test event with pass/fail status and artifact URLs
version_added: "1.0.0"
description:
  - Updates an existing test event with final test results, including pass/fail status,
    summary, and links to artifacts from the Ansible job.

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
  test_event_id:
    description:
      - ID of the test event to update
    type: str
    required: true
  status:
    description:
      - Test result status
    type: str
    required: true
    choices:
      - PASS
      - FAIL
  summary:
    description:
      - Summary of test results
    type: str
    required: true
  artifact_urls:
    description:
      - List of URLs to artifacts from the test run
    type: list
    elements: str
    required: false

author:
  - HATCI Contributors
"""

RETURN = r"""
test_event:
  description: Updated test event object
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
        test_event_id=dict(type="str", required=True),
        status=dict(type="str", required=True, choices=["PASS", "FAIL"]),
        summary=dict(type="str", required=True),
        artifact_urls=dict(type="list", elements="str", required=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    # Build update payload
    payload = {
        "status": module.params["status"],
        "summary": module.params["summary"],
    }

    if module.params.get("artifact_urls"):
        payload["artifact_urls"] = module.params["artifact_urls"]

    try:
        client = HATCIClient(
            base_url=module.params["hatci_base_url"],
            token=module.params["hatci_token"],
            verify_tls=module.params["verify_tls"],
            timeout=module.params["timeout"],
        )

        test_event_id = module.params["test_event_id"]
        response = client.patch(f"/api/v1/test_events/{test_event_id}", data=payload)

        module.exit_json(
            changed=True,
            test_event=response,
        )

    except HATCIClientError as e:
        module.fail_json(msg=str(e), changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}", changed=False)


if __name__ == "__main__":
    main()
