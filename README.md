# Simulated devices - static inventory and simulator data

This repository is a dedicated **Ansible Automation Platform (AAP) static inventory and source-data** project. It contains no dynamic inventory plugins or inventory scripts-only files you can sync from GitHub as a normal AAP **Project** (source control).

## Contents

- **`inventories/simulated_devices.yml`** - Static inventory. Every host uses `ansible_connection: local` and defines `simulator_name`, `jumpstarter_exporter_name`, `device_id`, and `device_type`.
- **`simulators/<simulator_name>/`** - File-backed twin/state/config and sample serial logs for demos. Automation playbooks can read paths such as `simulators/{{ simulator_name }}/twin.json` **relative to this repository’s root** after AAP syncs the project.
- **`exporters/`** - Mock Jumpstarter `ExporterConfig` YAML for local or simulated runs. **`endpoint` and `token` are empty placeholders**, not production secrets.

## Using simulator paths from another automation repo

Exact path wiring depends on how the Job Template combines projects:

1. **Single project checkout as working directory** - If this repo is the only (or primary) project and playbooks run with its root as CWD, use paths like `simulators/{{ simulator_name }}/twin.json` directly.
2. **Multiple projects** - If playbooks live in a separate automation project, align on a convention: e.g. set a variable to this project’s checkout path (how your team names it in AAP), then use `{{ simulator_data_project_path }}/simulators/{{ simulator_name }}/twin.json`, or use `include_vars` / `slurp` with a path your operators document. **Operators must match path expectations to their AAP project layout** (multiple checkouts, symlinks, or copied content).

Keep changes to simulator JSON/YAML in Git so the next **Project** sync updates AAP.

## Recommended AAP usage

1. Create an **AAP Project** pointing at this GitHub repository (branch or tag as appropriate).
2. Create an **Inventory** from `inventories/simulated_devices.yml` (static inventory import or project-sourced inventory, per your AAP workflow).
3. Attach that inventory to **Job Templates** (or workflow nodes) whose playbooks come from your main automation project.
4. Ensure the execution environment and playbook logic can **see this repo’s files** on the controller/execution node-whether via multiple projects, documented path variables, symlinks, or explicit lookups.

## Constraints

- No dynamic inventory plugin or `inventory/` scripts.
- Static data files only; no application code required.
