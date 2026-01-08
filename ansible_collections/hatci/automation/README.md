# Ansible Collection - hatci.automation

This collection orchestrates vehicle OTA (Over-The-Air) tests by integrating with two systems:

- **HATCI SUMS API**: Backend system of record for software updates
- **Jumpstarter**: Device control system running in local mode within the execution environment

## Overview

The `hatci.automation` collection provides modules and roles for:

1. **HATCI API Integration**: Creating, locking, deploying, and tracking OTA update events
2. **Jumpstarter Device Control**: Safely acquiring and releasing device leases during tests
3. **End-to-End Orchestration**: Complete workflows from preflight checks to result reporting

## Requirements

- Ansible 2.15 or later
- Red Hat Ansible Automation Platform (recommended)
- Execution environment with:
  - `jmp` CLI installed
  - Jumpstarter Python packages available
  - Network access to HATCI API
  - Writable directory for exporter configs (e.g., `/etc/jumpstarter/exporters.d`)

## Installation

Install the collection using Ansible Galaxy:

```bash
ansible-galaxy collection install hatci.automation
```

Or install from source:

```bash
cd ansible_collections/hatci/automation
ansible-galaxy collection build
ansible-galaxy collection install hatci-automation-*.tar.gz
```

## Dependencies

This collection depends on:

- `jumpstarter.jumpstarter` collection (for the `jumpstarter_lease` module)

Install it with:

```bash
ansible-galaxy collection install jumpstarter.jumpstarter
```

## Configuration

### HATCI API

Set the following environment variables or provide them as playbook variables:

- `HATCI_BASE_URL`: Base URL for HATCI API (e.g., `https://api.hatci.example.com`)
- `HATCI_TOKEN`: Authentication token for API requests

### Jumpstarter

Configure Jumpstarter client config inside the execution environment. The path should be accessible to the `jmp` CLI.

## Modules

### HATCI API Modules

All HATCI modules share common arguments:

- `hatci_base_url` (required): Base URL for HATCI API
- `hatci_token` (required): Authentication token
- `verify_tls` (default: `true`): Whether to verify TLS certificates
- `timeout` (default: `30`): Request timeout in seconds

#### hatci_create_event

Creates an OTA event (RROM or UROM) in HATCI SUMS.

```yaml
- name: Create source event
  hatci.automation.hatci_create_event:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    tester_name: "test_runner_01"
    program_name: "OTA_Test"
    model_year: "2024"
    vin: "1HGBH41JXMN109186"
    update_type: "RROM"
    region: "US"
    build_level: "2024.01.01"
    ecus:
      - ecu_name: "Gateway"
        part_number: "GW001"
        sw_version: "1.0.0"
```

#### hatci_fix_event

Locks an event so it can no longer be edited.

```yaml
- name: Fix event
  hatci.automation.hatci_fix_event:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    event_id: "event-12345"
```

#### hatci_deploy_event

Schedules and triggers an update deployment.

```yaml
- name: Deploy event
  hatci.automation.hatci_deploy_event:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    event_id: "event-12345"
    deployment_count: 1
```

#### hatci_update_status

Polls the backend for deployment or event status.

```yaml
- name: Check deployment status
  hatci.automation.hatci_update_status:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    deployment_id: "deploy-12345"
```

#### hatci_test_event

Creates a test event record linking vehicle, event, and Ansible job.

```yaml
- name: Create test event
  hatci.automation.hatci_test_event:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    vin: "1HGBH41JXMN109186"
    event_id: "event-12345"
    ansible_job_id: "{{ ansible_job_id }}"
    git_sha: "abc123def"
    suite_name: "ota_test"
```

#### hatci_test_event_update

Updates a test event with pass/fail status and artifact URLs.

```yaml
- name: Update test event
  hatci.automation.hatci_test_event_update:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    test_event_id: "test-event-12345"
    status: "PASS"
    summary: "OTA update completed successfully"
    artifact_urls:
      - "https://aap.example.com/jobs/12345/artifacts"
```

## Roles

### hatci_preflight

Validates HATCI API connectivity and required configuration.

```yaml
- hosts: localhost
  roles:
    - hatci.automation.hatci_preflight
```

### hatci_request_update

Creates and fixes both RROM and UROM events in a single workflow.

```yaml
- hosts: localhost
  vars:
    hatci_vin: "1HGBH41JXMN109186"
    hatci_tester_name: "test_runner"
    hatci_program_name: "OTA_Test"
    hatci_model_year: "2024"
    hatci_region: "US"
    hatci_source_build_level: "2024.01.01"
    hatci_target_build_level: "2024.02.01"
    hatci_source_ecus:
      - ecu_name: "Gateway"
        part_number: "GW001"
        sw_version: "1.0.0"
    hatci_target_ecus:
      - ecu_name: "Gateway"
        part_number: "GW001"
        sw_version: "2.0.0"
  roles:
    - hatci.automation.hatci_request_update
```

### hatci_wait_for_update

Polls for update completion with configurable timeout and interval.

```yaml
- hosts: localhost
  vars:
    hatci_deployment_id: "deploy-12345"
    hatci_poll_timeout_seconds: 3600
    hatci_poll_interval_seconds: 30
  roles:
    - hatci.automation.hatci_wait_for_update
```

### hatci_report_results

Updates test event with final results and artifact links.

```yaml
- hosts: localhost
  vars:
    hatci_test_event_id: "test-event-12345"
    hatci_test_status: "PASS"
    hatci_test_summary: "Update completed successfully"
  roles:
    - hatci.automation.hatci_report_results
```

### jumpstarter_exporter_config

Renders Jumpstarter exporter config from a Jinja2 template.

```yaml
- hosts: vehicle_001
  vars:
    jumpstarter_exporter_template: "{{ playbook_dir }}/templates/exporter.yaml.j2"
    jumpstarter_exporter_name: "vehicle_001"
  roles:
    - hatci.automation.jumpstarter_exporter_config
```

### jumpstarter_lease_guard

Safely acquires and releases device leases using block/rescue/always pattern.

```yaml
- name: Protected device operations
  block:
    - name: Acquire lease
      include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: main

    - name: Your device operations here
      ansible.builtin.debug:
        msg: "Device is leased"

  always:
    - name: Release lease
      include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: always
```

## Example Playbook

See `playbooks/ota_single_vehicle.yml` for a complete example that demonstrates:

1. Preflight validation
2. Exporter configuration
3. Test event creation
4. Lease acquisition and OTA update workflow
5. Status polling
6. Result reporting

## Architecture

### HATCI API Layer

The collection provides a stable API layer using a shared HTTP client (`hatci_client.py`) that handles:
- Authentication via Bearer tokens
- Request/response formatting
- Error handling
- TLS verification

### Jumpstarter Integration

Jumpstarter is treated as the system that controls physical devices. The collection:
- Templates exporter configs into writable directories inside the EE
- Uses the existing `jumpstarter_lease` module for device control
- Provides role-based wrappers for safe lease management

### Workflow Orchestration

Roles combine multiple API calls into reusable workflows:
- `hatci_request_update`: Creates and fixes both source and target events
- `hatci_wait_for_update`: Polls until completion with proper error handling
- `hatci_report_results`: Records test outcomes with artifact links

## Development

### Module Utils

The shared `hatci_client.py` module utility provides a clean interface for HTTP requests. It can be easily swapped out if needed (e.g., to use `requests` library instead of `urllib`).

### Error Handling

All modules use consistent error handling:
- `HATCIClientError` for API-specific errors
- Clear error messages with context
- Proper HTTP status code handling

### Testing

Modules are designed to work with real APIs. For testing:
- Use mock HTTP servers or API testing tools
- Provide valid test credentials
- Verify TLS certificate handling

## License

GPL-2.0-or-later

## Author Information

HATCI Contributors

## Support

For issues and questions, please refer to the project repository or contact the maintainers.
