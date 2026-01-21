#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: hatci_fix_event
short_description: Lock an event so it can no longer be edited
version_added: "1.0.0"
description:
  - Locks a HATCI event by marking it as "fixed", preventing further modifications.
  - This must be done before deploying an event.

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
      - ID of the event to fix/lock
    type: str
    required: true

author:
  - Alex Benavides <abenavid@redhat.com>
"""

RETURN = r"""
fixed:
  description: Whether the event was successfully fixed
  returned: always
  type: bool
event:
  description: Updated event object
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
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    event_id = module.params["event_id"]

    try:
        client = HATCIClient(
            base_url=module.params["hatci_base_url"],
            token=module.params["hatci_token"],
            verify_tls=module.params["verify_tls"],
            timeout=module.params["timeout"],
        )

        # Fix the event (lock it)
        response = client.post(f"/api/v1/events/{event_id}/fix", data={})

        fixed = response.get("fixed", False)
        if not fixed:
            # Some APIs might return success without explicit "fixed" field
            fixed = response.get("status") == "fixed" or "fixed" in str(response).lower()

        module.exit_json(
            changed=True,
            fixed=fixed,
            event=response,
        )

    except HATCIClientError as e:
        module.fail_json(msg=str(e), changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}", changed=False)


if __name__ == "__main__":
    main()
