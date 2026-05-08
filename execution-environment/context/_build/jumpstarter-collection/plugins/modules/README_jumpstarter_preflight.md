# jumpstarter_preflight

Purpose  
Run first in a playbook to validate Jumpstarter is usable inside the execution environment.

What it checks  
1. `jmp` exists in PATH and `jmp version` works  
2. Optional: expected config directories exist  
3. Optional: exporter name exists in `jmp get exporters -o json`

Typical usage

```yaml
- hosts: localhost
  gather_facts: false
  collections:
    - jumpstarter.jumpstarter
  tasks:
    - name: Preflight
      jumpstarter_preflight:
        exporter: test

    - name: Power cycle
      jumpstarter_power:
        exporter: test
        state: cycle
        wait: 1
