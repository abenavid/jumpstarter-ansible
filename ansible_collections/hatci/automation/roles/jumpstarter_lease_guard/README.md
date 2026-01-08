# jumpstarter_lease_guard

This role provides a safe way to acquire and release a Jumpstarter device lease for the duration of a test block.

## Purpose

Ensures that a device lease is always released, even if tasks fail. This role should be used with Ansible's `block`/`rescue`/`always` pattern to guarantee cleanup.

## Requirements

- The `jumpstarter.jumpstarter.jumpstarter_lease` module must be available
- `jmp` CLI must be installed in the execution environment

## Role Variables

### Required

- `jumpstarter_exporter_selector`: Selector for lease acquisition (e.g., `"exporter=vehicle_001"`)

### Optional

- `jumpstarter_lease_duration`: Lease duration (default: `"30m"`)
- `jumpstarter_client_config`: Path to client config file inside EE
- `jumpstarter_client`: Named client to use (alternative to client_config)

## Usage Pattern

This role is designed to be used with the block/rescue/always pattern:

```yaml
- name: Acquire lease and run protected tasks
  block:
    - name: Acquire lease
      include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: main

    - name: Your protected tasks here
      ansible.builtin.debug:
        msg: "Device is leased, safe to use"

  always:
    - name: Release lease
      include_role:
        name: hatci.automation.jumpstarter_lease_guard
        tasks_from: always
```

## Facts Set

- `current_lease_name`: Name of the acquired lease (available after main tasks)

## Notes

- The lease is acquired in the main tasks and released in the always tasks
- If lease acquisition fails, the role will fail with a clear error message
- The always tasks will attempt to release the lease even if main tasks fail
