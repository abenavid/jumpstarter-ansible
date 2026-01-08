## Jumpstarter Ansible Collection

This repository contains an Ansible collection that makes
[Jumpstarter](https://jumpstarter.dev/main/index.html) more accessible from
playbooks by exposing common `jmp`/`j` workflows as first‑class Ansible
modules.

Jumpstarter is a free and open source testing tool that bridges the gap
between development workflows and deployment environments. It lets you test
your software stack consistently across real hardware and virtual
environments using cloud‑native principles.

This collection is designed to be used inside an Ansible Execution
Environment (EE) where:

- The `jmp` CLI and Jumpstarter drivers are installed (for example via
  `pip install -r context/_build/requirements.txt` into the EE image).
- Exporter configuration files are available in
  `/etc/jumpstarter/exporters/*.yaml`, as described in `ARCHITECTURE.md`.

### Collection name

- **Fully qualified collection name (FQCN)**:
  `jumpstarter.jumpstarter`

### Exporters and capabilities

Each Jumpstarter *exporter* YAML file (for example `exporters/test.yaml`) defines
which device capabilities are available:

- **`export.power`**: Enables `j power ...` commands (and thus the
  `jumpstarter_power` module).
- **`export.storage`**: Enables storage operations such as `j storage ...`.
- **`export.serial`**: Enables serial-console related commands.

The Ansible modules in this collection do **not** hard-code capabilities; they
simply send `j` commands to `jmp shell --exporter <name>`. If an exporter does
not define a required driver (for example no `export.power`), the corresponding
commands will fail at runtime.

### Provided modules (initial set)

- **`jumpstarter_shell`**: Run one or more `j` commands through
  `jmp shell --exporter <name>` and capture output.
- **`jumpstarter_power`**: Convenience wrapper around `j power` to switch
  devices on/off or cycle power via Jumpstarter.
- **`jumpstarter_jmp`**: Low-level wrapper around the `jmp` CLI for running
  generic commands like `jmp get exporters`, `jmp get leases`, `jmp version`,
  etc. (see the `jmp` man page at
  [Jumpstarter docs](https://jumpstarter.dev/main/reference/man-pages/jmp.html#)).

You can build additional higher‑level modules on top of these helpers as
needed for your hardware.

### Example: run arbitrary Jumpstarter shell commands

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  tasks:
    - name: Cycle power via generic shell module
      jumpstarter.jumpstarter.jumpstarter_shell:
        exporter: test
        commands:
          - "j power cycle --wait 1"
      register: result

    - debug:
        var: result.stdout
```

### Example: power module

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  tasks:
    - name: Ensure device power cycled
      jumpstarter.jumpstarter.jumpstarter_power:
        exporter: test
        state: cycle
        wait: 1
```

### Example: generic jmp commands

```yaml
- hosts: localhost
  collections:
    - jumpstarter.jumpstarter

  tasks:
    - name: List exporters as JSON
      jumpstarter.jumpstarter.jumpstarter_jmp:
        args:
          - get
          - exporters
          - -o
          - json
      register: exporters

    - name: Show exporters info
      ansible.builtin.debug:
        var: exporters.stdout
```

### Usage in an Execution Environment

Combined with the `execution-environment.yml` and exporter configuration
from this repository, a typical flow is:

1. Build an EE image that includes:
   - Ansible Core and this collection.
   - Jumpstarter CLI (`jmp`) and drivers.
   - Exporter YAML files copied into
     `/etc/jumpstarter/exporters/`, for example `test.yaml`.
2. Run playbooks with `ansible-navigator` or AAP against the EE image.
3. Use `jumpstarter_shell` or `jumpstarter_power` tasks to control devices
   through the configured Jumpstarter exporters.

See `ARCHITECTURE.md` for a detailed diagram of how Jumpstarter fits into
the EE.


