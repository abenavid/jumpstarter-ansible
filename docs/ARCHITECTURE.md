# Jumpstarter + Ansible Execution Environment Architecture

This diagram illustrates how Jumpstarter is integrated into an Ansible Execution Environment to manage edge devices on vehicles.

```mermaid
graph TB
    subgraph "Build Time"
        EE[Ansible Execution Environment<br/>execution-environment.yml]
        EXP[Exporter Configurations<br/>exporters/*.yaml]
        EE -->|"ansible-builder build"| IMG[Container Image<br/>jumpstarter-ee:v1]
        EXP -->|"COPY to /etc/jumpstarter/exporters"| IMG
    end

    subgraph "Container Image Contents"
        IMG --> EE_CONTENTS[Execution Environment Container]
        EE_CONTENTS --> ANSIBLE[Ansible Core<br/>+ Collections]
        EE_CONTENTS --> JMP_CLI[Jumpstarter CLI<br/>jmp command]
        EE_CONTENTS --> DRIVERS[Jumpstarter Drivers<br/>- power<br/>- storage<br/>- serial<br/>- composite]
        EE_CONTENTS --> EXP_CFG[Exporter Configs<br/>/etc/jumpstarter/exporters]
    end

    subgraph "Runtime - Ansible Playbook Execution"
        PLAYBOOK[Ansible Playbook<br/>test.yml]
        PLAYBOOK -->|"ansible-navigator run"| EE_RUNTIME[EE Container Runtime]
        EE_RUNTIME --> ANSIBLE
        EE_RUNTIME --> JMP_CLI
        EE_RUNTIME --> DRIVERS
        EE_RUNTIME --> EXP_CFG
    end

    subgraph "Jumpstarter Command Flow"
        ANSIBLE -->|"command: jmp shell --exporter test"| JMP_CLI
        JMP_CLI -->|"reads config"| EXP_CFG
        JMP_CLI -->|"uses driver"| DRIVERS
    end

    subgraph "Edge Devices on Vehicles"
        DRIVERS -->|"Power Control"| POWER[Vehicle Power Systems]
        DRIVERS -->|"Serial Communication"| SERIAL[Edge Device Serial Ports]
        DRIVERS -->|"Storage Access"| STORAGE[Device Storage/File Systems]
    end

    subgraph "Vehicle Network"
        POWER --> VEHICLE[Vehicle Edge Device]
        SERIAL --> VEHICLE
        STORAGE --> VEHICLE
    end

    style IMG fill:#e1f5ff
    style EE_CONTENTS fill:#fff4e1
    style PLAYBOOK fill:#e8f5e9
    style VEHICLE fill:#ffebee
    style JMP_CLI fill:#f3e5f5
    style DRIVERS fill:#f3e5f5
```

## Component Details

### 1. Execution Environment Build
- **Base Image**: Red Hat Ansible Automation Platform 25 (ee-minimal-rhel9)
- **Jumpstarter Installation**: CLI and drivers installed via pip from `pkg.jumpstarter.dev`
- **Exporter Configs**: Copied from `exporters/` directory to `/etc/jumpstarter/exporters` in container

### 2. Exporter Configuration
Each exporter YAML file defines:
- **Power Driver**: Controls device power (e.g., `MockPower`, real power controllers)
- **Storage Driver**: Manages device storage (e.g., `MockStorageMux`, OpenDAL backends)
- **Serial Driver**: Handles serial communication (e.g., `PySerial` with device URLs)

### 3. Ansible Playbook Execution
- Playbooks run inside the EE container
- Use `jmp` CLI commands via Ansible's `command` module
- Commands reference exporter configs by name (e.g., `--exporter test`)

### 4. Device Management Flow
1. Ansible playbook executes `jmp` command
2. Jumpstarter CLI reads exporter configuration
3. Appropriate driver interfaces with vehicle edge device
4. Power, serial, and storage operations are performed on the device

## Example Usage

```yaml
# test.yml
- hosts: localhost
  tasks:
    - name: Cycle power using Jumpstarter
      command: jmp shell --exporter test
      args:
        stdin: "j power cycle --wait 1\n"
```

This playbook:
1. Runs inside the EE container
2. Executes `jmp shell --exporter test`
3. Jumpstarter reads `/etc/jumpstarter/exporters/test.yaml`
4. Uses configured drivers to cycle power on the edge device

