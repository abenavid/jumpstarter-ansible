# Getting Started with hatci.automation

This guide will help you get started with the `hatci.automation` collection for orchestrating vehicle OTA tests.

## Prerequisites

1. **Ansible 2.15+** installed
2. **Red Hat Ansible Automation Platform** (recommended) or Ansible Core
3. **Execution Environment** with:
   - `jmp` CLI installed
   - Jumpstarter Python packages
   - Network access to HATCI API
   - Writable directory for exporter configs

4. **Dependencies**:
   ```bash
   ansible-galaxy collection install jumpstarter.jumpstarter
   ```

## Quick Start

### 1. Install the Collection

```bash
ansible-galaxy collection install hatci.automation
```

Or from source:

```bash
cd ansible_collections/hatci/automation
ansible-galaxy collection build
ansible-galaxy collection install hatci-automation-*.tar.gz
```

### 2. Configure HATCI API Access

Set environment variables:

```bash
export HATCI_BASE_URL="https://api.hatci.example.com"
export HATCI_TOKEN="your-token-here"
```

Or provide them in your playbook:

```yaml
vars:
  hatci_base_url: "https://api.hatci.example.com"
  hatci_token: "{{ vault_hatci_token }}"
```

### 3. Configure Jumpstarter

Ensure Jumpstarter client config is available in your execution environment:

```yaml
vars:
  jumpstarter_client_config: "/private/etc/jumpstarter/client.yaml"
```

### 4. Create an Exporter Template

Create a Jinja2 template for your vehicle exporter config:

```yaml
# templates/vehicle_exporter.yaml.j2
name: {{ jumpstarter_exporter_name }}
device:
  address: {{ device_address }}
  serial_url: {{ serial_url | default('') }}
power:
  control: {{ power_control }}
```

### 5. Run Your First Playbook

Use the example playbook as a starting point:

```bash
ansible-playbook -i inventory playbooks/ota_single_vehicle.yml
```

## Common Workflows

### Basic OTA Update Flow

1. **Preflight**: Validate API connectivity
2. **Configure Exporter**: Template Jumpstarter config
3. **Create Test Event**: Record test run
4. **Acquire Lease**: Get device access
5. **Request Update**: Create and fix events
6. **Deploy**: Trigger deployment
7. **Wait**: Poll for completion
8. **Report**: Update test event with results
9. **Release Lease**: Clean up

### Minimal Example

```yaml
- hosts: localhost
  vars:
    hatci_base_url: "https://api.hatci.example.com"
    hatci_token: "{{ vault_hatci_token }}"
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

  tasks:
    - name: Preflight
      include_role:
        name: hatci.automation.hatci_preflight

    - name: Request update
      include_role:
        name: hatci.automation.hatci_request_update

    - name: Deploy
      hatci.automation.hatci_deploy_event:
        hatci_base_url: "{{ hatci_base_url }}"
        hatci_token: "{{ hatci_token }}"
        event_id: "{{ target_event_id }}"

    - name: Wait for completion
      include_role:
        name: hatci.automation.hatci_wait_for_update
      vars:
        hatci_deployment_id: "{{ deployment_result.deployment_id }}"
```

## Troubleshooting

### API Connection Issues

If you see "Network error" or "API is not reachable":

1. Verify `HATCI_BASE_URL` is correct
2. Check network connectivity from execution environment
3. Verify TLS certificates if using HTTPS
4. Test with `hatci_preflight` role

### Authentication Errors

If you see "HTTP 401" or "HTTP 403":

1. Verify `HATCI_TOKEN` is valid and not expired
2. Check token has required permissions
3. Ensure token is not being logged (use `no_log: true` in vars)

### Lease Acquisition Failures

If lease acquisition fails:

1. Verify Jumpstarter is running in local mode
2. Check `jmp` CLI is available in execution environment
3. Verify exporter selector matches configured exporters
4. Check device availability

### Module Import Errors

If you see import errors:

1. Verify collection is installed: `ansible-galaxy collection list`
2. Check collection namespace matches: `hatci.automation`
3. Ensure module_utils path is correct

## Next Steps

- Review the [example playbook](playbooks/ota_single_vehicle.yml)
- Explore individual [module documentation](../README.md#modules)
- Check [role documentation](../README.md#roles)
- Customize workflows for your specific use case
