# hatci_wait_for_update

This role polls the HATCI API for update status until completion or failure.

## Purpose

Monitors a deployment or event until it reaches a terminal state (COMPLETE or FAILED). The role will fail the play if the update doesn't complete within the timeout or ends in a failed state.

## Requirements

- HATCI API access
- Valid authentication token
- Event or deployment ID to monitor

## Role Variables

### Required

- `hatci_base_url`: Base URL for HATCI API
- `hatci_token`: Authentication token
- Either `hatci_event_id` or `hatci_deployment_id`: ID to monitor

### Optional

- `hatci_poll_timeout_seconds`: Maximum time to wait (default: `3600` = 1 hour)
- `hatci_poll_interval_seconds`: Time between polls (default: `30`)
- `hatci_verify_tls`: TLS verification (default: `true`)
- `hatci_timeout`: Request timeout (default: `30`)
- `hatci_success_states`: List of states indicating success (default: `['COMPLETE', 'COMPLETED', 'SUCCESS']`)
- `hatci_failure_states`: List of states indicating failure (default: `['FAILED', 'ERROR', 'CANCELLED']`)

## Example Usage

```yaml
- hosts: localhost
  vars:
    hatci_deployment_id: "deploy-12345"
    hatci_poll_timeout_seconds: 7200
    hatci_poll_interval_seconds: 60
  roles:
    - hatci.automation.hatci_wait_for_update
```

## Facts Set

- `hatci_final_state`: Final state of the update
- `hatci_final_reason`: Reason for failure (if applicable)
- `hatci_final_timestamps`: Dictionary of relevant timestamps

## Notes

- The role uses Ansible's `until` loop with retries for polling
- If timeout is reached, the role will fail
- If the update ends in a failure state, the role will fail
- Polling continues until a terminal state is reached or timeout occurs
