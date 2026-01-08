# Collection Structure

This document describes the structure of the `hatci.automation` collection.

## Directory Layout

```
hatci/automation/
├── galaxy.yml                    # Collection metadata
├── README.md                     # Main collection documentation
├── meta/
│   └── runtime.yml              # Runtime requirements (Ansible >= 2.15.0)
├── plugins/
│   ├── modules/                 # Python modules for HATCI API
│   │   ├── hatci_create_event.py
│   │   ├── hatci_fix_event.py
│   │   ├── hatci_deploy_event.py
│   │   ├── hatci_update_status.py
│   │   ├── hatci_test_event.py
│   │   └── hatci_test_event_update.py
│   ├── module_utils/            # Shared utilities
│   │   └── hatci_client.py     # HTTP client for HATCI API
│   └── inventory/               # Dynamic inventory plugin (stub)
│       └── hatci.py
├── roles/                       # Reusable roles
│   ├── hatci_preflight/        # API connectivity validation
│   ├── hatci_request_update/   # Create and fix RROM/UROM events
│   ├── hatci_wait_for_update/  # Poll for update completion
│   ├── hatci_report_results/   # Update test event with results
│   ├── jumpstarter_exporter_config/  # Template exporter configs
│   └── jumpstarter_lease_guard/      # Safe lease acquisition/release
├── playbooks/                   # Example playbooks
│   └── ota_single_vehicle.yml  # Complete OTA workflow example
├── templates/                   # Jinja2 templates
│   └── exporter.yaml.j2        # Example exporter config template
└── docs/                        # Additional documentation
    └── GETTING_STARTED.md       # Getting started guide
```

## Components

### Modules (plugins/modules/)

All HATCI API modules share common arguments:
- `hatci_base_url`: Base URL for API
- `hatci_token`: Authentication token
- `verify_tls`: TLS verification (default: true)
- `timeout`: Request timeout (default: 30)

**HATCI API Modules:**
1. `hatci_create_event` - Create RROM or UROM events
2. `hatci_fix_event` - Lock events for deployment
3. `hatci_deploy_event` - Schedule and trigger deployments
4. `hatci_update_status` - Poll for status updates
5. `hatci_test_event` - Create test event records
6. `hatci_test_event_update` - Update test events with results

### Module Utils (plugins/module_utils/)

- `hatci_client.py`: Shared HTTP client with authentication, error handling, and TLS support

### Roles (roles/)

**HATCI Roles:**
- `hatci_preflight`: Validates API connectivity and configuration
- `hatci_request_update`: Creates and fixes both source and target events
- `hatci_wait_for_update`: Polls until update completes or fails
- `hatci_report_results`: Records test outcomes with artifact links

**Jumpstarter Roles:**
- `jumpstarter_exporter_config`: Templates exporter configs into EE
- `jumpstarter_lease_guard`: Safe lease acquisition/release pattern

### Inventory Plugin (plugins/inventory/)

- `hatci.py`: Stub implementation for future dynamic inventory from HATCI API

### Example Playbook (playbooks/)

- `ota_single_vehicle.yml`: Complete example demonstrating the full OTA workflow

## Dependencies

- `jumpstarter.jumpstarter` collection (>=0.1.0) - Required for `jumpstarter_lease` module

## Usage Patterns

### Basic Module Usage

```yaml
- name: Create event
  hatci.automation.hatci_create_event:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_token }}"
    # ... module-specific parameters
```

### Role Usage

```yaml
- hosts: localhost
  roles:
    - hatci.automation.hatci_preflight
```

### Block Pattern for Lease Guard

```yaml
- name: Protected operations
  block:
    - include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: main
    - name: Your tasks here
      # ...
  always:
    - include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: always
```

## Testing

Modules are designed to work with real APIs. For testing:
- Use mock HTTP servers
- Provide valid test credentials
- Verify TLS certificate handling
- Test error scenarios

## Future Enhancements

- Implement full dynamic inventory plugin
- Add more HATCI API endpoints as needed
- Enhance error handling and retry logic
- Add support for batch operations
