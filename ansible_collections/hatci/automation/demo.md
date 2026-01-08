# HATCI Automation Collection - Demo Walkthrough

## Overview

The `hatci.automation` collection orchestrates vehicle OTA (Over-The-Air) update tests by integrating two critical systems:

1. **HATCI SUMS API** - Backend system of record for software updates
2. **Jumpstarter** - Physical device control system running in the execution environment

This collection provides a complete automation framework for managing the full lifecycle of OTA update testing, from creating update events to reporting test results.

## What This Collection Does

### High-Level Purpose

The collection automates the complex workflow of:
- Creating software update events (source and target versions)
- Locking events for deployment
- Scheduling and monitoring deployments
- Safely controlling physical test vehicles via Jumpstarter
- Tracking test runs and reporting results

### Key Capabilities

**HATCI API Integration:**
- Create and manage OTA update events (RROM/UROM)
- Lock events to prevent modifications
- Deploy updates to vehicles
- Poll for deployment status
- Record test runs and outcomes

**Jumpstarter Device Control:**
- Template exporter configurations into the execution environment
- Safely acquire and release device leases
- Ensure devices are always released, even on failure

**Workflow Orchestration:**
- Preflight validation (API connectivity, configuration)
- End-to-end update workflows
- Status monitoring with timeouts
- Automatic result reporting

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│         Ansible Automation Platform / Playbook              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│              hatci.automation Collection                   │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ HATCI API    │              │ Jumpstarter  │            │
│  │ Modules      │              │ Roles        │            │
│  │              │              │              │            │
│  │ • create     │              │ • exporter   │            │
│  │ • fix        │              │ • lease      │            │
│  │ • deploy     │              │   guard      │            │
│  │ • status     │              │              │            │
│  │ • test_event │              │              │            │
│  └──────────────┘              └──────────────┘            │
└────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐        ┌──────────────────────┐
│  HATCI SUMS API  │        │  Jumpstarter (local) │
│  (Backend)       │        │  • jmp CLI            │
│                  │        │  • Exporter configs   │
│                  │        │  • Device leases      │
└──────────────────┘        └──────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  Test Vehicle    │
                            │  (Physical HW)   │
                            └──────────────────┘
```

## Typical Workflow

### 1. Preflight Validation
Validate that HATCI API is reachable and all required configuration is present.

### 2. Configure Jumpstarter Exporter
Template the exporter configuration file for the specific test vehicle into the execution environment.

### 3. Create Test Event Record
Register the test run in HATCI with vehicle, job, and metadata information.

### 4. Acquire Device Lease
Safely acquire a Jumpstarter lease for the test vehicle.

### 5. Request OTA Update
Create source (RROM) and target (UROM) events, then lock both.

### 6. Deploy Update
Schedule and trigger the deployment to the vehicle.

### 7. Monitor Progress
Poll HATCI API until deployment completes or fails.

### 8. Verify Results
(Placeholder for UI interaction, diagnostics collection, etc.)

### 9. Report Results
Update the test event with pass/fail status and artifact links.

### 10. Release Lease
Always release the device lease, even if previous steps failed.

## High-Level Examples

### Example 1: Simple OTA Update Request

This example shows how to create and fix both source and target events:

```yaml
- hosts: localhost
  vars:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    hatci_vin: "1HGBH41JXMN109186"
    hatci_tester_name: "automation_runner"
    hatci_program_name: "OTA_Test_Program"
    hatci_model_year: "2024"
    hatci_region: "US"
    
    # Source version (current)
    hatci_source_build_level: "2024.01.01"
    hatci_source_ecus:
      - ecu_name: "Gateway"
        part_number: "GW-2024-001"
        sw_version: "1.0.0"
    
    # Target version (desired)
    hatci_target_build_level: "2024.02.01"
    hatci_target_ecus:
      - ecu_name: "Gateway"
        part_number: "GW-2024-001"
        sw_version: "2.0.0"

  tasks:
    - name: Request OTA update (creates and fixes both events)
      include_role:
        name: hatci.automation.hatci_request_update
      
    - name: Display event IDs
      ansible.builtin.debug:
        msg:
          - "Source event: {{ source_event_id }}"
          - "Target event: {{ target_event_id }}"
```

**What happens:**
- Creates RROM (source) event with current software versions
- Creates UROM (target) event with desired software versions
- Locks both events so they can be deployed
- Returns `source_event_id` and `target_event_id` as facts

### Example 2: Complete OTA Workflow with Device Control

This example demonstrates the full workflow including Jumpstarter device control:

```yaml
- hosts: vehicle_001
  vars:
    # HATCI API configuration
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    
    # Vehicle information
    hatci_vin: "1HGBH41JXMN109186"
    hatci_tester_name: "automation_runner"
    hatci_program_name: "OTA_Test"
    hatci_model_year: "2024"
    hatci_region: "US"
    
    # Version information
    hatci_source_build_level: "2024.01.01"
    hatci_target_build_level: "2024.02.01"
    hatci_source_ecus:
      - ecu_name: "Gateway"
        part_number: "GW-2024-001"
        sw_version: "1.0.0"
    hatci_target_ecus:
      - ecu_name: "Gateway"
        part_number: "GW-2024-001"
        sw_version: "2.0.0"
    
    # Jumpstarter configuration
    jumpstarter_exporter_name: "vehicle_001"
    jumpstarter_exporter_template: "{{ playbook_dir }}/templates/vehicle_exporter.yaml.j2"
    jumpstarter_lease_duration: "60m"
    jumpstarter_client_config: "/private/etc/jumpstarter/client.yaml"

  tasks:
    - name: Preflight checks
      include_role:
        name: hatci.automation.hatci_preflight

    - name: Configure Jumpstarter exporter
      include_role:
        name: hatci.automation.jumpstarter_exporter_config

    - name: Create test event record
      hatci.automation.hatci_test_event:
        hatci_base_url: "{{ hatci_base_url }}"
        hatci_token: "{{ hatci_token }}"
        vin: "{{ hatci_vin }}"
        event_id: "pending"
        ansible_job_id: "{{ ansible_job_id | default('manual') }}"
        git_sha: "{{ lookup('env', 'GIT_SHA') | default('unknown') }}"
        suite_name: "ota_complete_workflow"
      register: test_event

    - name: Protected device operations
      block:
        - name: Acquire device lease
          include_role:
            name: hatci.automation.jumpstarter_lease_guard
            tasks_from: main

        - name: Request OTA update
          include_role:
            name: hatci.automation.hatci_request_update

        - name: Deploy target event
          hatci.automation.hatci_deploy_event:
            hatci_base_url: "{{ hatci_base_url }}"
            hatci_token: "{{ hatci_token }}"
            event_id: "{{ target_event_id }}"
          register: deployment

        - name: Wait for update completion
          include_role:
            name: hatci.automation.hatci_wait_for_update
          vars:
            hatci_deployment_id: "{{ deployment.deployment_id }}"
            hatci_poll_timeout_seconds: 3600

        - name: Collect diagnostics via Jumpstarter
          jumpstarter.jumpstarter.jumpstarter_shell:
            exporter: "{{ jumpstarter_exporter_name }}"
            commands:
              - "j serial read --timeout 5"
          register: diagnostics

      always:
        - name: Release device lease
          include_role:
            name: hatci.automation.jumpstarter_lease_guard
            tasks_from: always

    - name: Report test results
      include_role:
        name: hatci.automation.hatci_report_results
      vars:
        hatci_test_event_id: "{{ test_event.test_event_id }}"
        hatci_test_status: "{{ 'PASS' if hatci_final_state in ['COMPLETE'] else 'FAIL' }}"
        hatci_test_summary: "OTA update completed with state: {{ hatci_final_state }}"
```

**What happens:**
1. Validates API connectivity
2. Creates exporter config for the vehicle
3. Registers test run in HATCI
4. Acquires device lease (guaranteed release in `always` block)
5. Creates and fixes update events
6. Deploys the update
7. Polls until completion
8. Collects diagnostics via Jumpstarter
9. Reports results to HATCI
10. Always releases the lease

### Example 3: Status Monitoring

Monitor an existing deployment:

```yaml
- hosts: localhost
  vars:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
    hatci_deployment_id: "deploy-12345"

  tasks:
    - name: Wait for deployment completion
      include_role:
        name: hatci.automation.hatci_wait_for_update
      vars:
        hatci_poll_timeout_seconds: 7200  # 2 hours
        hatci_poll_interval_seconds: 60   # Check every minute

    - name: Display final status
      ansible.builtin.debug:
        msg:
          - "State: {{ hatci_final_state }}"
          - "Reason: {{ hatci_final_reason | default('N/A') }}"
```

**What happens:**
- Polls HATCI API every 60 seconds
- Continues until deployment reaches terminal state (COMPLETE/FAILED)
- Fails if timeout is reached or deployment fails
- Sets facts with final status information

### Example 4: Jumpstarter Exporter Configuration

Template a custom exporter configuration:

```yaml
- hosts: vehicle_001
  vars:
    jumpstarter_exporter_name: "vehicle_001"
    jumpstarter_exporter_template: "{{ playbook_dir }}/templates/custom_exporter.yaml.j2"
    
    # Template variables
    device_address: "192.168.1.100"
    serial_url: "tcp://192.168.1.100:23"
    power_control: "ipmi"
    power_address: "192.168.1.101"

  tasks:
    - name: Configure exporter
      include_role:
        name: hatci.automation.jumpstarter_exporter_config

    - name: Use the configured exporter
      jumpstarter.jumpstarter.jumpstarter_power:
        exporter: "{{ jumpstarter_exporter_name }}"
        state: on
```

**What happens:**
- Creates exporter config file in `/etc/jumpstarter/exporters.d/`
- Config file is available to `jmp` CLI immediately
- Can be used with any Jumpstarter module

### Example 5: Safe Lease Management Pattern

Demonstrates the block/rescue/always pattern for guaranteed cleanup:

```yaml
- hosts: vehicle_001
  vars:
    jumpstarter_exporter_selector: "exporter=vehicle_001"
    jumpstarter_lease_duration: "30m"

  tasks:
    - name: Protected device operations
      block:
        - name: Acquire lease
          include_role:
            name: hatci.automation.jumpstarter_lease_guard
            tasks_from: main

        - name: Power on device
          jumpstarter.jumpstarter.jumpstarter_power:
            exporter: vehicle_001
            state: on

        - name: Run device tests
          # ... your test tasks here ...
          ansible.builtin.debug:
            msg: "Running tests on leased device"

        - name: Power off device
          jumpstarter.jumpstarter.jumpstarter_power:
            exporter: vehicle_001
            state: off

      rescue:
        - name: Handle errors
          ansible.builtin.debug:
            msg: "Error occurred, but lease will still be released"

      always:
        - name: Release lease (always runs)
          include_role:
            name: hatci.automation.jumpstarter_lease_guard
            tasks_from: always
```

**What happens:**
- Lease is acquired at the start of the block
- Device operations run
- If any task fails, rescue block handles it
- **Always** block guarantees lease release, even on failure

## Integration with Jumpstarter Collection

The `hatci.automation` collection works seamlessly with `jumpstarter.jumpstarter`:

### Jumpstarter Provides:
- **Device Control**: Power, serial, storage operations
- **Lease Management**: `jumpstarter_lease` module for device access
- **Exporter System**: YAML-based device configuration

### HATCI Automation Adds:
- **Workflow Orchestration**: Higher-level roles that combine operations
- **Safe Patterns**: Guaranteed lease release via `jumpstarter_lease_guard`
- **Configuration Management**: Dynamic exporter config templating
- **HATCI Integration**: Complete OTA update lifecycle management

### Combined Usage Example

```yaml
- name: OTA update with device verification
  block:
    - name: Acquire lease
      include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: main

    - name: Request and deploy update
      include_role:
        name: hatci.automation.hatci_request_update
      # ... deploy and wait ...

    - name: Verify update on device
      jumpstarter.jumpstarter.jumpstarter_shell:
        exporter: "{{ jumpstarter_exporter_name }}"
        commands:
          - "j serial send 'check_version'"
          - "j serial read --timeout 10"

  always:
    - name: Release lease
      include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: always
```

## Key Benefits

1. **Separation of Concerns**: HATCI handles update management, Jumpstarter handles device control
2. **Safety**: Guaranteed lease release prevents device lockups
3. **Reusability**: Roles can be combined in different workflows
4. **Traceability**: All operations recorded in HATCI test events
5. **Error Handling**: Consistent patterns for failure scenarios
6. **Flexibility**: Works with any Jumpstarter exporter configuration

## Next Steps

- Review the [example playbook](playbooks/ota_single_vehicle.yml) for a complete implementation
- Check [Getting Started Guide](docs/GETTING_STARTED.md) for setup instructions
- Explore individual [module documentation](README.md#modules) for detailed options
- Customize workflows for your specific vehicle and test requirements

## Common Patterns

### Pattern 1: Preflight → Update → Report
```yaml
- hatci_preflight
- hatci_request_update
- hatci_deploy_event
- hatci_wait_for_update
- hatci_report_results
```

### Pattern 2: Device-Protected Update
```yaml
block:
  - jumpstarter_lease_guard (acquire)
  - hatci_request_update
  - hatci_deploy_event
  - hatci_wait_for_update
always:
  - jumpstarter_lease_guard (release)
```

### Pattern 3: Full Lifecycle
```yaml
- hatci_preflight
- jumpstarter_exporter_config
- hatci_test_event (create)
- block:
    - jumpstarter_lease_guard (acquire)
    - hatci_request_update
    - hatci_deploy_event
    - hatci_wait_for_update
  always:
    - jumpstarter_lease_guard (release)
- hatci_report_results
```

These patterns can be combined and customized based on your specific testing requirements.
