# hatci_report_results

This role updates a HATCI test event with final pass/fail status and artifact links.

## Purpose

Records the outcome of a test run in HATCI by updating the test event with:
- Final test status (PASS or FAIL)
- Summary of results
- URLs to artifacts from the Ansible job

## Requirements

- HATCI API access
- Valid authentication token
- Test event ID from `hatci_test_event` module

## Role Variables

### Required

- `hatci_base_url`: Base URL for HATCI API
- `hatci_token`: Authentication token
- `hatci_test_event_id`: ID of the test event to update
- `hatci_test_summary`: Summary of test results

### Optional

- `hatci_test_status`: Test status (default: `"PASS"`, can be `"PASS"` or `"FAIL"`)
- `hatci_artifact_urls`: List of artifact URLs (default: `[]`)
- `hatci_verify_tls`: TLS verification (default: `true`)
- `hatci_timeout`: Request timeout (default: `30`)

## Automatic Status Detection

The role will automatically set status to `FAIL` if any tasks failed during the playbook run (based on `ansible_failed_tasks`).

## Example Usage

```yaml
- hosts: localhost
  vars:
    hatci_test_event_id: "test-event-12345"
    hatci_test_summary: "OTA update completed successfully. All ECUs updated to target version."
    hatci_artifact_urls:
      - "https://aap.example.com/jobs/12345/artifacts"
  roles:
    - hatci.automation.hatci_report_results
```

## Integration with Ansible Automation Platform

If `ansible_job_url` is available (from AAP context), it will be automatically added to artifact URLs.

## Notes

- This role should typically be called at the end of a playbook or in an `always` block
- Status can be explicitly set or will be inferred from playbook outcome
- Artifact URLs should be full URLs accessible from outside the execution environment
