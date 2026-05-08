# File-backed simulators

## Where state lives

Simulator **twin** and **state** JSON files are updated on the execution environment during a playbook run. By default, that data exists only in the EE filesystem for the lifetime of the job. The next run starts from whatever is already in your inventory project (or collection paths), not from the previous run’s runtime copy—unless you enable Git persistence below.

## Persisting state back to Git (AAP)

The `demo_select_simulator` playbook can optionally copy updated twin/state files into the **same** Git repository and branch used by the inventory source (for example `inventory` on `https://github.com/abenavid/jumpstarter-ansible.git`), then commit and push.

Enable this with extra variables (or host/group vars):

- `simulator_commit_state_to_git: true`

When enabled, the playbook runs the **`simulator_git_persist`** role at the end of the workflow. That role:

1. Requires **`GIT_USERNAME`** and **`GIT_TOKEN`** in the process environment (see below). Values are read with `lookup('env', 'GIT_USERNAME')` and `lookup('env', 'GIT_TOKEN')`.
2. Configures `git config user.name` and `user.email` in the project checkout.
3. Sets `origin` to an authenticated HTTPS URL built from those credentials and **`simulator_git_remote_url`**, then **fetches**, **checks out** **`simulator_state_branch`**, and **pulls** `origin/<branch>`.
4. Ensures **`runtime_state/simulated_devices/<inventory_hostname>/`** exists and copies each host’s updated **`twin.json`** / **`state.json`** (paths come from the simulator roles).
5. Runs **`git add`** on **`runtime_state/`** (see **`simulator_state_git_staged_path`**), **`git commit`**, and **`git push`** to **`origin`** on the same branch.
6. Restores **`origin`** to the credential-free **`simulator_git_remote_url`** after the push.

Sensitive steps use **`no_log: true`** so tokens and authenticated URLs are not written to job output.

If there is **nothing to commit** (clean index after `git add`), the shell step exits **0** and the playbook does **not** fail. Failures are reserved for real Git errors (merge conflicts, auth, missing branch, etc.).

### Intended use

This path is for **demos** and **lightweight persistence** so an inventory branch can reflect the last simulated device state. **Production** or multi-tenant automation should use a **database**, **device registry**, or **API** as the source of truth—not commits from automation jobs.

### AAP credentials and environment variables

Attach a credential to the job template that injects:

| Variable        | Role |
|-----------------|------|
| `GIT_USERNAME`  | Git user for HTTPS (often your GitHub username; PAT “username” schemes vary by provider) |
| `GIT_TOKEN`     | Personal access token (or equivalent) with **push** access to the repo |

Do **not** put the token in extra variables or inventory where it could be logged. Rely on AAP **Credential** → **Environment variables** (or your EE’s supported injection mechanism).

The role temporarily sets:

`git remote set-url origin https://<GIT_USERNAME>:<GIT_TOKEN>@github.com/...`

matching **`simulator_git_remote_url`**, then restores the remote URL without credentials after **`git push`**.

### Runtime layout after a successful push

```text
runtime_state/
  simulated_devices/
    sim_vehicle_001/
      twin.json
      state.json
    sim_gateway_001/
      twin.json
      state.json
```

Runtime exports are intentionally kept under **`runtime_state/`**, separate from **source** simulator definitions elsewhere in the repo.

### Related variables

Defaults live in `ansible_collections/jumpstarter/jumpstarter/roles/simulator_git_persist/defaults/main.yml`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `simulator_commit_state_to_git` | `false` | Enable Git persistence |
| `simulator_state_branch` | `inventory` | Branch to checkout and push (branch must **already exist**) |
| `simulator_state_repo_path` | `/runner/project` | Git repo root (AAP project dir; override locally to your checkout) |
| `simulator_state_output_dir` | `runtime_state/simulated_devices` | Relative path for per-host exports |
| `simulator_state_git_staged_path` | `runtime_state` | Path passed to `git add` |
| `simulator_git_remote_url` | `https://github.com/abenavid/jumpstarter-ansible.git` | Credential-free URL restored after push |
| `simulator_git_user_name` | `AAP Simulator Bot` | `git config user.name` |
| `simulator_git_user_email` | `aap-simulator@example.com` | `git config user.email` |

### Example job extra variables

```yaml
simulator_commit_state_to_git: true
# Optional overrides:
# simulator_state_repo_path: /runner/project
# simulator_state_branch: inventory
# simulator_git_remote_url: https://github.com/abenavid/jumpstarter-ansible.git
```

Credentials (`GIT_USERNAME`, `GIT_TOKEN`) should come from the job’s **credential**, not from this YAML.

### Example commit message

```text
Update simulator state from AAP job 4815162342
```

If `tower_job_id` / `awx_job_id` are unset (e.g. local `ansible-playbook`), the suffix falls back to an ISO8601-style timestamp from **`ansible_date_time`**.

## Troubleshooting

- **Concurrent jobs:** With Git persistence enabled, **do not** run multiple concurrent jobs that push to the **same** branch. Serialize jobs or use a single fork; otherwise `git pull` / `git push` races can cause conflicts or lost updates.
- **Git PAT:** The token must allow **write** (push) to the target repository.
- **Inventory branch:** **`simulator_state_branch`** must already exist on the remote; the role does not create it.
- **Layout:** Runtime twin/state under **`runtime_state/`** is separate from checked-in simulator **definitions**; do not mix the two trees without a deliberate layout change.
- **Local runs:** Keep `simulator_commit_state_to_git: false` unless you set **`simulator_state_repo_path`** to a real checkout, export **`GIT_USERNAME`** / **`GIT_TOKEN`**, and accept pushes to your remote.

## Concurrency warning (summary)

If `simulator_commit_state_to_git` is enabled, treat the inventory branch as a **single-writer** resource from AAP’s perspective, or disable persistence where overlap is possible.
