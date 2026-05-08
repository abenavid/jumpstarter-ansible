# jumpstarter.collect_diagnostics

Collects diagnostic artifacts from inside an Ansible Execution Environment that has Jumpstarter installed.

## What it collects

Always:
- jmp path and whether it exists
- jmp version output (if present)
- summary.json with key booleans and return codes

Optional:
- exporters.json via `jmp get exporters ... -o json`
- leases.json via `jmp get leases ... -o json`
- environment.txt with basic system and Ansible versions
- extra_commands.txt for any custom checks you provide
- a tar.gz archive of the run directory

## Variables

- `jumpstarter_diagnostics_output_dir` (default: `/tmp/jumpstarter_diagnostics`)
- `jumpstarter_diagnostics_create_archive` (default: `true`)
- `jumpstarter_diagnostics_archive_path` (default: empty, role generates one)
- `jumpstarter_diagnostics_client_config` (default: empty)
- `jumpstarter_diagnostics_client` (default: empty)
- `jumpstarter_diagnostics_skip_queries_without_client` (default: true)
- `jumpstarter_diagnostics_query_exporters` (default: true)
- `jumpstarter_diagnostics_query_leases` (default: true)
- `jumpstarter_diagnostics_capture_env` (default: true)
- `jumpstarter_diagnostics_extra_commands` (default: empty list)

## Output

The role sets:
- `jumpstarter_diagnostics_result.run_dir`
- `jumpstarter_diagnostics_result.archive_path`
- `jumpstarter_diagnostics_result.jmp_present`
- `jumpstarter_diagnostics_result.ran_queries`
