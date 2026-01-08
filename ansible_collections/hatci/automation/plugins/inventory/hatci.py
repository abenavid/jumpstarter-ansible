#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) HATCI Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
HATCI Dynamic Inventory Plugin (Stub)

This is a placeholder for a future dynamic inventory plugin that will
discover vehicles and test targets from the HATCI API.

Currently returns an empty inventory structure.
"""

from __future__ import annotations

DOCUMENTATION = r"""
---
plugin: hatci
short_description: HATCI dynamic inventory (stub)
version_added: "1.0.0"
description:
  - Placeholder for future HATCI dynamic inventory plugin
  - Currently returns empty inventory
options:
  hatci_base_url:
    description: Base URL for HATCI API
    type: str
    required: true
  hatci_token:
    description: Authentication token
    type: str
    required: true
    env:
      - name: HATCI_TOKEN
  verify_tls:
    description: Whether to verify TLS certificates
    type: bool
    default: true
"""

from ansible.plugins.inventory import BaseInventoryPlugin

try:
    from ansible_collections.hatci.automation.plugins.module_utils.hatci_client import (
        HATCIClient,
    )
except ImportError:
    # Fallback for development
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from module_utils.hatci_client import HATCIClient


class InventoryModule(BaseInventoryPlugin):
    """HATCI dynamic inventory plugin (stub implementation)."""

    NAME = "hatci.automation.hatci"

    def verify_file(self, path: str) -> bool:
        """Return true if this is a HATCI inventory file."""
        return path.endswith(("hatci.yml", "hatci.yaml", "hatci_plugin.yml", "hatci_plugin.yaml"))

    def parse(self, inventory, loader, path, cache=True):
        """Parse inventory and add hosts."""
        super().parse(inventory, loader, path)

        # Read configuration
        config = self._read_config_data(path)
        self._consume_options(config)

        # Get configuration values
        base_url = self.get_option("hatci_base_url")
        token = self.get_option("hatci_token")
        verify_tls = self.get_option("verify_tls")

        # TODO: Implement actual inventory discovery from HATCI API
        # For now, return empty inventory structure

        # Example structure (commented out):
        # client = HATCIClient(base_url=base_url, token=token, verify_tls=verify_tls)
        # vehicles = client.get("/api/v1/vehicles")
        # for vehicle in vehicles:
        #     self.inventory.add_host(vehicle["vin"])
        #     self.inventory.set_variable(vehicle["vin"], "hatci_vehicle_id", vehicle["id"])

        # Stub: Add a placeholder group
        self.inventory.add_group("hatci_vehicles")
        # No hosts added yet - this is a stub
