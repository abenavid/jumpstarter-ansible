# hatci_preflight

This role validates that the HATCI API is reachable and required configuration is present before starting OTA operations.

## Purpose

Performs early validation to fail fast with clear error messages if:
- HATCI API is not reachable
- Required environment variables or vars are missing
- Vehicle metadata cannot be loaded

## Requirements

- Network access to HATCI API
- Valid HATCI authentication token

## Role Variables

### Required (via vars or environment)

- `hatci_base_url`: Base URL for HATCI API (or `HATCI_BASE_URL` env var)
- `hatci_token`: Authentication token (or `HATCI_TOKEN` env var)

### Optional

- `hatci_verify_tls`: Whether to verify TLS certificates (default: `true`)
- `hatci_timeout`: Request timeout in seconds (default: `30`)
- `hatci_vin`: Vehicle Identification Number for metadata validation

## Example Usage

```yaml
- hosts: localhost
  vars:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
  roles:
    - hatci.automation.hatci_preflight
```

## Facts Set

- `hatci_vehicle_metadata_loaded`: Set to `true` if VIN was provided and metadata was loaded

## Notes

- This role will fail early if API is unreachable or credentials are invalid
- Environment variables are checked as fallback if vars are not provided
