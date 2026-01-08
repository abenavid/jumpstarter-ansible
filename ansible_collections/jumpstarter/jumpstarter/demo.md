# Jumpstarter Ansible Collection - Demo Walkthrough

## Overview

The `jumpstarter.jumpstarter` collection makes [Jumpstarter](https://jumpstarter.dev/main/index.html) accessible from Ansible playbooks by exposing common `jmp`/`j` workflows as first-class Ansible modules.

Jumpstarter is a free and open source testing tool that bridges the gap between development workflows and deployment environments. It lets you test your software stack consistently across real hardware and virtual environments using cloud-native principles.

## What This Collection Does

### High-Level Purpose

The collection provides Ansible-native interfaces for:
- **Device Power Control**: Turn devices on, off, or cycle power
- **Serial Console Operations**: Read from and write to device serial consoles
- **Storage Operations**: Manage device storage and file operations
- **Lease Management**: Acquire, renew, and release device leases
- **Generic Shell Commands**: Run any Jumpstarter `j` command through the shell
- **Low-Level CLI Access**: Execute arbitrary `jmp` commands

### Key Capabilities

**Device Control:**
- Power management (on, off, cycle)
- Serial console interaction
- Storage operations
- Generic shell command execution

**Lease Management:**
- Acquire device leases with selectors
- Renew existing leases
- Release leases when done
- Support for client configs and named clients

**Preflight & Validation:**
- Verify `jmp` CLI availability
- Check exporter configurations
- Validate execution environment setup

**Wait & Retry Logic:**
- Wait for devices to reach ready state
- Retry with exponential backoff
- Support for custom readiness checks

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│         Ansible Automation Platform / Playbook              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           jumpstarter.jumpstarter Collection                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Modules     │  │    Roles     │  │   Utils      │     │
│  │               │  │              │  │              │     │
│  │ • power       │  │ • collect_    │  │ • common     │     │
│  │ • shell       │  │   diagnostics │  │              │     │
│  │ • lease       │  │              │  │              │     │
│  │ • jmp         │  │              │  │              │     │
│  │ • wait        │  │              │  │              │     │
│  │ • preflight   │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Jumpstarter (jmp CLI)                          │
│  ┌──────────────┐              ┌──────────────┐             │
│  │  Exporter    │              │   Drivers    │             │
│  │  Configs     │              │              │             │
│  │              │              │ • Power     │             │
│  │ • test.yaml  │              │ • Serial    │             │
│  │ • device.yaml│              │ • Storage   │             │
│  └──────────────┘              └──────────────┘             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Physical Devices                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Device 1    │  │   Device 2    │  │   Device N    │   │
│  │               │  │               │  │               │   │
│  │ • Power       │  │ • Power       │  │ • Power       │   │
│  │ • Serial      │  │ • Serial      │  │ • Serial      │   │
│  │ • Storage     │  │ • Storage     │  │ • Storage     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Execution Environment Setup

This collection is designed to run inside an Ansible Execution Environment (EE) where:

1. **Jumpstarter CLI (`jmp`) is installed** via pip or package manager
2. **Jumpstarter drivers are available** (power, serial, storage drivers)
3. **Exporter configurations** are mounted or copied into `/etc/jumpstarter/exporters/`
4. **Client configuration** (optional) is available for multi-tenant setups

## Modules Overview

### jumpstarter_power

Control device power states (on, off, cycle).

**Key Features:**
- Simple state-based interface
- Optional wait time after power operations
- Works with any exporter that defines `export.power`

### jumpstarter_shell

Run arbitrary Jumpstarter `j` commands through `jmp shell`.

**Key Features:**
- Execute single or multiple commands
- Capture stdout/stderr
- Access to all Jumpstarter capabilities (power, serial, storage)

### jumpstarter_lease

Manage device leases for exclusive access.

**Key Features:**
- Acquire leases with selectors (e.g., `exporter=test`)
- Renew leases before expiration
- Release leases when done
- Support for client configs and named clients

### jumpstarter_jmp

Low-level wrapper for arbitrary `jmp` CLI commands.

**Key Features:**
- Run any `jmp` subcommand
- Query exporters, leases, versions
- Full access to Jumpstarter management API

### jumpstarter_wait

Wait for devices to reach ready state with retries.

**Key Features:**
- Retry logic with exponential backoff
- Custom readiness checks (serial prompts, files, commands)
- Detailed attempt history

### jumpstarter_preflight

Validate execution environment and exporter availability.

**Key Features:**
- Verify `jmp` CLI is available
- Check exporter configurations exist
- Validate specific exporters are available
- Early failure detection

## High-Level Examples

### Example 1: Simple Power Control

Basic power operations on a device:

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  vars:
    exporter_name: test

  tasks:
    - name: Power cycle the device
      jumpstarter.jumpstarter.jumpstarter_power:
        exporter: "{{ exporter_name }}"
        state: cycle
        wait: 2

    - name: Ensure device is powered on
      jumpstarter.jumpstarter.jumpstarter_power:
        exporter: "{{ exporter_name }}"
        state: on
        wait: 5
```

**What happens:**
- Cycles power (off → on) with 2 second wait
- Ensures device is on with 5 second wait for boot
- Uses the `test` exporter configuration

### Example 2: Serial Console Interaction

Read from and write to device serial console:

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  vars:
    exporter_name: test

  tasks:
    - name: Send command to serial console
      jumpstarter.jumpstarter.jumpstarter_shell:
        exporter: "{{ exporter_name }}"
        commands:
          - "j serial send 'uname -a'"
          - "j serial read --timeout 5"

    - name: Read serial output
      jumpstarter.jumpstarter.jumpstarter_shell:
        exporter: "{{ exporter_name }}"
        command: "j serial read --timeout 10"
      register: serial_output

    - name: Display serial output
      ansible.builtin.debug:
        var: serial_output.stdout
```

**What happens:**
- Sends command to device serial console
- Reads response with timeout
- Captures output for further processing

### Example 3: Lease Management Pattern

Safely acquire and release device leases:

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  vars:
    exporter_name: test
    lease_duration: "30m"
    client_config: "/private/etc/jumpstarter/client.yaml"

  tasks:
    - name: Acquire device lease
      jumpstarter.jumpstarter.jumpstarter_lease:
        state: acquire
        selector: "exporter={{ exporter_name }}"
        duration: "{{ lease_duration }}"
        client_config: "{{ client_config }}"
        output: name
      register: lease_result

    - name: Display lease information
      ansible.builtin.debug:
        msg: "Acquired lease: {{ lease_result.lease_name }}"

    - name: Perform device operations
      block:
        - name: Power on device
          jumpstarter.jumpstarter.jumpstarter_power:
            exporter: "{{ exporter_name }}"
            state: on
            wait: 5

        - name: Run device tests
          jumpstarter.jumpstarter.jumpstarter_shell:
            exporter: "{{ exporter_name }}"
            commands:
              - "j serial send 'test_command'"
              - "j serial read --timeout 10"

      always:
        - name: Release lease
          jumpstarter.jumpstarter.jumpstarter_lease:
            state: release
            lease_name: "{{ lease_result.lease_name }}"
            client_config: "{{ client_config }}"
```

**What happens:**
- Acquires exclusive lease for 30 minutes
- Performs device operations while lease is active
- Always releases lease in `always` block (even on failure)

### Example 4: Preflight Validation

Validate environment before operations:

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  vars:
    exporter_name: test
    client_config: "/private/etc/jumpstarter/client.yaml"

  tasks:
    - name: Preflight checks
      jumpstarter.jumpstarter.jumpstarter_preflight:
        exporter: "{{ exporter_name }}"
        client_config: "{{ client_config }}"
        fail_on_missing_exporter: true
        check_config_dirs: true
      register: preflight_result

    - name: Display preflight information
      ansible.builtin.debug:
        msg:
          - "jmp version: {{ preflight_result.jmp_version }}"
          - "jmp present: {{ preflight_result.jmp_present }}"
          - "Exporter found: {{ preflight_result.exporter_found }}"

    - name: Continue with device operations
      jumpstarter.jumpstarter.jumpstarter_power:
        exporter: "{{ exporter_name }}"
        state: on
      when: preflight_result.exporter_found | default(false)
```

**What happens:**
- Verifies `jmp` CLI is available
- Checks exporter configuration exists
- Validates specific exporter is available
- Fails early if validation fails

### Example 5: Wait for Device Ready

Wait for device to reach ready state:

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  vars:
    exporter_name: test

  tasks:
    - name: Power cycle device
      jumpstarter.jumpstarter.jumpstarter_power:
        exporter: "{{ exporter_name }}"
        state: cycle
        wait: 2

    - name: Wait for device to be ready
      jumpstarter.jumpstarter.jumpstarter_wait:
        exporter: "{{ exporter_name }}"
        check_shell_cmd: "j serial read --timeout 2 | grep -q 'login:'"
        success_regex: "login:"
        retries: 20
        delay: 2
        backoff: 1.5
      register: wait_result

    - name: Display wait attempts
      ansible.builtin.debug:
        msg:
          - "Device ready after {{ wait_result.attempts | length }} attempts"
          - "Total time: {{ wait_result.total_time_seconds }}s"

    - name: Continue with operations
      jumpstarter.jumpstarter.jumpstarter_shell:
        exporter: "{{ exporter_name }}"
        command: "j serial send 'whoami'"
```

**What happens:**
- Powers cycles the device
- Waits for serial console to show login prompt
- Retries with exponential backoff (starts at 2s, increases by 1.5x)
- Continues when device is ready or fails after 20 attempts

### Example 6: Generic jmp Commands

Query Jumpstarter system information:

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  vars:
    client_config: "/private/etc/jumpstarter/client.yaml"

  tasks:
    - name: Get all exporters
      jumpstarter.jumpstarter.jumpstarter_jmp:
        args:
          - get
          - exporters
          - -o
          - json
        client_config: "{{ client_config }}"
      register: exporters

    - name: Get active leases
      jumpstarter.jumpstarter.jumpstarter_jmp:
        args:
          - get
          - leases
          - -o
          - json
        client_config: "{{ client_config }}"
      register: leases

    - name: Get Jumpstarter version
      jumpstarter.jumpstarter.jumpstarter_jmp:
        args:
          - version
          - -o
          - json
      register: version

    - name: Display system information
      ansible.builtin.debug:
        msg:
          - "Exporters: {{ exporters.stdout | from_json | map(attribute='name') | list }}"
          - "Active leases: {{ leases.stdout | from_json | length }}"
          - "Version: {{ version.stdout | from_json }}"
```

**What happens:**
- Queries available exporters
- Lists active leases
- Gets Jumpstarter version information
- Displays formatted results

### Example 7: Complete Device Test Workflow

End-to-end device testing workflow:

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  vars:
    exporter_name: test
    lease_duration: "60m"
    client_config: "/private/etc/jumpstarter/client.yaml"

  tasks:
    - name: Preflight validation
      jumpstarter.jumpstarter.jumpstarter_preflight:
        exporter: "{{ exporter_name }}"
        client_config: "{{ client_config }}"
        fail_on_missing_exporter: true

    - name: Acquire device lease
      jumpstarter.jumpstarter.jumpstarter_lease:
        state: acquire
        selector: "exporter={{ exporter_name }}"
        duration: "{{ lease_duration }}"
        client_config: "{{ client_config }}"
        output: name
      register: lease

    - name: Device test workflow
      block:
        - name: Power on device
          jumpstarter.jumpstarter.jumpstarter_power:
            exporter: "{{ exporter_name }}"
            state: on
            wait: 5

        - name: Wait for device ready
          jumpstarter.jumpstarter.jumpstarter_wait:
            exporter: "{{ exporter_name }}"
            check_shell_cmd: "j serial read --timeout 2 | grep -q 'ready'"
            success_regex: "ready"
            retries: 30
            delay: 3

        - name: Run test commands
          jumpstarter.jumpstarter.jumpstarter_shell:
            exporter: "{{ exporter_name }}"
            commands:
              - "j serial send 'test_command_1'"
              - "j serial read --timeout 5"
              - "j serial send 'test_command_2'"
              - "j serial read --timeout 5"
          register: test_results

        - name: Collect diagnostics
          jumpstarter.jumpstarter.jumpstarter_shell:
            exporter: "{{ exporter_name }}"
            commands:
              - "j serial send 'collect_logs'"
              - "j serial read --timeout 10"

        - name: Power off device
          jumpstarter.jumpstarter.jumpstarter_power:
            exporter: "{{ exporter_name }}"
            state: off

      rescue:
        - name: Handle test failures
          ansible.builtin.debug:
            msg: "Test failed, but lease will be released"

      always:
        - name: Release device lease
          jumpstarter.jumpstarter.jumpstarter_lease:
            state: release
            lease_name: "{{ lease.lease_name }}"
            client_config: "{{ client_config }}"
```

**What happens:**
1. Validates environment and exporter availability
2. Acquires exclusive lease for 60 minutes
3. Powers on device and waits for ready state
4. Runs test commands via serial console
5. Collects diagnostic information
6. Powers off device
7. Always releases lease (even on failure)

## Roles

### collect_diagnostics

Collects diagnostic artifacts from the execution environment.

**What it collects:**
- `jmp` path and version information
- Exporter configurations (JSON)
- Active leases (JSON)
- Environment information
- Custom diagnostic commands
- Creates tar.gz archive of diagnostics

**Example usage:**

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  tasks:
    - name: Collect Jumpstarter diagnostics
      include_role:
        name: jumpstarter.jumpstarter.collect_diagnostics
      vars:
        jumpstarter_diagnostics_output_dir: "/tmp/diagnostics"
        jumpstarter_diagnostics_query_exporters: true
        jumpstarter_diagnostics_query_leases: true
        jumpstarter_diagnostics_client_config: "/private/etc/jumpstarter/client.yaml"

    - name: Display diagnostics location
      ansible.builtin.debug:
        msg: "Diagnostics archive: {{ jumpstarter_diagnostics_result.archive_path }}"
```

## Common Patterns

### Pattern 1: Simple Power Control
```yaml
- jumpstarter_power (state: on/off/cycle)
```

### Pattern 2: Serial Console Interaction
```yaml
- jumpstarter_shell (commands: ["j serial send ...", "j serial read ..."])
```

### Pattern 3: Safe Lease Management
```yaml
block:
  - jumpstarter_lease (acquire)
  - [device operations]
always:
  - jumpstarter_lease (release)
```

### Pattern 4: Preflight → Operations
```yaml
- jumpstarter_preflight
- jumpstarter_power / jumpstarter_shell
```

### Pattern 5: Power → Wait → Operations
```yaml
- jumpstarter_power (cycle)
- jumpstarter_wait (ready check)
- jumpstarter_shell (test commands)
```

### Pattern 6: Complete Workflow
```yaml
- jumpstarter_preflight
- jumpstarter_lease (acquire)
- block:
    - jumpstarter_power (on)
    - jumpstarter_wait (ready)
    - jumpstarter_shell (operations)
  always:
    - jumpstarter_lease (release)
```

## Exporter Configuration

Exporters define device capabilities. Example exporter config:

```yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
metadata:
  name: test
endpoint: ""
token: ""
export:
  power:
    type: jumpstarter_driver_power.driver.MockPower
  storage:
    type: jumpstarter_driver_opendal.driver.MockStorageMux
  serial:
    type: jumpstarter_driver_pyserial.driver.PySerial
    config:
      url: "loop://"
```

**Capabilities:**
- `export.power`: Enables power control (`j power ...`)
- `export.serial`: Enables serial console (`j serial ...`)
- `export.storage`: Enables storage operations (`j storage ...`)

Modules automatically use available capabilities based on exporter configuration.

## Key Benefits

1. **Ansible-Native**: First-class Ansible modules, not shell scripts
2. **Execution Environment Ready**: Designed for containerized execution
3. **Flexible**: Works with any exporter configuration
4. **Safe**: Lease management prevents device conflicts
5. **Robust**: Preflight checks and wait/retry logic
6. **Extensible**: Generic shell and jmp modules for custom operations

## Integration with Other Collections

### With hatci.automation

The `hatci.automation` collection uses `jumpstarter.jumpstarter` for device control:

```yaml
- name: OTA update workflow
  block:
    - name: Acquire lease (via hatci role)
      include_role:
        name: hatci.automation.jumpstarter_lease_guard
    
    - name: Device operations via Jumpstarter
      jumpstarter.jumpstarter.jumpstarter_power:
        exporter: vehicle_001
        state: on
      
      jumpstarter.jumpstarter.jumpstarter_shell:
        exporter: vehicle_001
        commands:
          - "j serial send 'verify_update'"
          - "j serial read --timeout 10"
```

## Best Practices

1. **Always use preflight** for early failure detection
2. **Use leases** for exclusive device access
3. **Always release leases** in `always` blocks
4. **Use wait modules** after power operations
5. **Check exporter capabilities** before operations
6. **Collect diagnostics** for troubleshooting

## Next Steps

- Review [example playbooks](examples/) for more patterns
- Check [README](README.md) for detailed module documentation
- Explore exporter configurations in `exporters/` directory
- Build custom execution environment with Jumpstarter installed
- Integrate with your test automation workflows

## Troubleshooting

### Module fails with "exporter not found"
- Verify exporter config exists in `/etc/jumpstarter/exporters/`
- Check exporter name matches configuration file name
- Use `jumpstarter_preflight` to validate

### Lease acquisition fails
- Check device availability
- Verify selector syntax (e.g., `exporter=test`)
- Ensure client config is correct (if using)

### Power operations fail
- Verify exporter defines `export.power` driver
- Check device connectivity
- Review Jumpstarter logs

### Serial operations fail
- Verify exporter defines `export.serial` driver
- Check serial URL configuration
- Ensure device serial console is accessible
