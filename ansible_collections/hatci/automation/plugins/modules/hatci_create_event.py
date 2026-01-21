#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: hatci_create_event
short_description: Create an OTA event (RROM or UROM) in HATCI SUMS
version_added: "1.0.0"
description:
  - Creates a source event (RROM) or target event (UROM) in the HATCI SUMS API.
  - This is the first step in the OTA update workflow.

options:
  hatci_base_url:
    description:
      - Base URL for HATCI API (e.g., https://api.hatci.example.com)
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
  tester_name:
    description:
      - Name of the tester
    type: str
    required: true
  program_name:
    description:
      - Program name
    type: str
    required: true
  model_year:
    description:
      - Vehicle model year
    type: str
    required: true
  vin:
    description:
      - Vehicle Identification Number
    type: str
    required: true
  update_type:
    description:
      - Type of update event
    type: str
    required: true
    choices:
      - RROM
      - UROM
  region:
    description:
      - Region identifier
    type: str
    required: true
  region_spec:
    description:
      - Region specification
    type: str
    required: false
  build_level:
    description:
      - Build level identifier
    type: str
    required: true
  remark:
    description:
      - Optional remarks or notes
    type: str
    required: false
  ecus:
    description:
      - List of ECUs included in this event
    type: list
    elements: dict
    required: true
    suboptions:
      ecu_name:
        description:
          - Name of the ECU
        type: str
        required: true
      part_number:
        description:
          - Part number of the ECU
        type: str
        required: true
      sw_version:
        description:
          - Software version
        type: str
        required: true

author:
  - Alex Benavides <abenavid@redhat.com>

notes:
  - This module requires network access to the HATCI API.
"""

RETURN = r"""
event_id:
  description: Unique identifier for the created event
  returned: always
  type: str
event:
  description: Full event object returned from the API
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
    # Fallback for development/testing
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
        tester_name=dict(type="str", required=True),
        program_name=dict(type="str", required=True),
        model_year=dict(type="str", required=True),
        vin=dict(type="str", required=True),
        update_type=dict(type="str", required=True, choices=["RROM", "UROM"]),
        region=dict(type="str", required=True),
        region_spec=dict(type="str", required=False),
        build_level=dict(type="str", required=True),
        remark=dict(type="str", required=False),
        ecus=dict(type="list", elements="dict", required=True),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    # Build request payload
    payload = {
        "tester_name": module.params["tester_name"],
        "program_name": module.params["program_name"],
        "model_year": module.params["model_year"],
        "vin": module.params["vin"],
        "update_type": module.params["update_type"],
        "region": module.params["region"],
        "build_level": module.params["build_level"],
        "ecus": module.params["ecus"],
    }

    if module.params.get("region_spec"):
        payload["region_spec"] = module.params["region_spec"]
    if module.params.get("remark"):
        payload["remark"] = module.params["remark"]

    # Initialize client and make request
    try:
        client = HATCIClient(
            base_url=module.params["hatci_base_url"],
            token=module.params["hatci_token"],
            verify_tls=module.params["verify_tls"],
            timeout=module.params["timeout"],
        )

        response = client.post("/api/v1/events", data=payload)

        event_id = response.get("event_id") or response.get("id")
        if not event_id:
            module.fail_json(msg="API response missing event_id", response=response)

        module.exit_json(
            changed=True,
            event_id=event_id,
            event=response,
        )

    except HATCIClientError as e:
        module.fail_json(msg=str(e), changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}", changed=False)


if __name__ == "__main__":
    main()
