# jumpstarter_exporter_config

This role renders a Jumpstarter exporter configuration file from a Jinja2 template into a writable directory inside the execution environment.

## Purpose

Jumpstarter exporter configs need to be available to the `jmp` CLI running inside the execution environment. Instead of trying to mount new volumes mid-job, this role templates the config into a directory that's already writable (e.g., `/etc/jumpstarter/exporters.d`).

## Requirements

- A Jinja2 template file for the exporter configuration
- The exporters directory must be writable inside the execution environment

## Role Variables

### Required

- `jumpstarter_exporter_template`: Path to the Jinja2 template file for the exporter config

### Optional

- `jumpstarter_exporter_name`: Name of the exporter (default: `{{ inventory_hostname }}`)
- `jumpstarter_exporters_dir`: Directory where configs are written (default: `/etc/jumpstarter/exporters.d`)
- `jumpstarter_exporter_cleanup`: Whether to clean up the config after completion (default: `false`)

## Example Usage

```yaml
- hosts: vehicle_001
  vars:
    jumpstarter_exporter_template: "{{ playbook_dir }}/templates/vehicle_exporter.yaml.j2"
    jumpstarter_exporter_name: "vehicle_001"
  roles:
    - hatci.automation.jumpstarter_exporter_config
```

## Template Variables

Your exporter template can use any Ansible variables. Common variables include:

- `device_address`: Network address or serial URL
- `power_control`: Power control configuration
- `serial_url`: Serial connection URL
- Any other device-specific configuration

## Facts Set

- `jumpstarter_exporter_config_path`: Full path to the created exporter config file
