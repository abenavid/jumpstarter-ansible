from __future__ import annotations

import subprocess
from typing import List, Tuple


def run_jmp_shell(
    exporter: str,
    commands: List[str],
    timeout: int | None = None,
) -> Tuple[int, str, str, str]:
    """
    Run one or more `j` commands via `jmp shell --exporter <exporter>`.

    The commands are joined with newlines and a final newline is appended so
    that the shell receives a complete input stream.
    """
    if not commands:
        raise ValueError("commands list must not be empty")

    stdin_payload = "\n".join(commands) + "\n"

    cmd = ["jmp", "shell", "--exporter", exporter]

    completed = subprocess.run(  # nosec B603,B607 - controlled CLI wrapper
        cmd,
        input=stdin_payload,
        text=True,
        capture_output=True,
        timeout=timeout,
    )

    return completed.returncode, completed.stdout, completed.stderr, " ".join(cmd)


def run_jmp(
    args: List[str],
    timeout: int | None = None,
) -> Tuple[int, str, str, str]:
    """
    Run an arbitrary `jmp` command with the given argument list.

    Example:

        run_jmp(["get", "exporters", "-o", "json"])
    """
    cmd = ["jmp", *args]

    completed = subprocess.run(  # nosec B603,B607 - controlled CLI wrapper
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
    )

    return completed.returncode, completed.stdout, completed.stderr, " ".join(cmd)

