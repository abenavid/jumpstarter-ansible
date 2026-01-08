# hatci_request_update

This role combines event creation and fixing into a single reusable workflow for OTA updates.

## Purpose

Creates both RROM (source) and UROM (target) events, then fixes (locks) both events so they can be deployed. This is a common pattern in OTA workflows.

## Requirements

- HATCI API access
- Valid authentication token
- All required vehicle and version information

## Role Variables

### Required

- `hatci_base_url`: Base URL for HATCI API
- `hatci_token`: Authentication token
- `hatci_vin`: Vehicle Identification Number
- `hatci_tester_name`: Name of the tester
- `hatci_program_name`: Program name
- `hatci_model_year`: Vehicle model year
- `hatci_region`: Region identifier
- `hatci_source_build_level`: Build level for source (RROM) event
- `hatci_target_build_level`: Build level for target (UROM) event
- `hatci_source_ecus`: List of ECUs for source event
- `hatci_target_ecus`: List of ECUs for target event

### Optional

- `hatci_region_spec`: Region specification
- `hatci_source_remark`: Remarks for source event
- `hatci_target_remark`: Remarks for target event
- `hatci_verify_tls`: TLS verification (default: `true`)
- `hatci_timeout`: Request timeout (default: `30`)

## ECU Format

ECUs should be provided as a list of dictionaries:

```yaml
hatci_source_ecus:
  - ecu_name: "ECU1"
    part_number: "PN12345"
    sw_version: "1.0.0"
  - ecu_name: "ECU2"
    part_number: "PN67890"
    sw_version: "2.0.0"
```

## Example Usage

```yaml
- hosts: localhost
  vars:
    hatci_vin: "1HGBH41JXMN109186"
    hatci_tester_name: "test_runner_01"
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

## Facts Set

- `source_event_id`: ID of the created and fixed RROM event
- `target_event_id`: ID of the created and fixed UROM event

## Notes

- Both events are created and fixed in sequence
- The role will fail if any step fails
- Event IDs are available as facts after role completion
