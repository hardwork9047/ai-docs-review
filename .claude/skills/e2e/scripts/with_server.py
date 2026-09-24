#!/usr/bin/env python3
"""Start one or more dev servers, wait for their ports, run a command, then clean up.

Usage:
    with_server.py --server "cd frontend && pnpm dev" --port 5173 -- <command...>
    with_server.py --server "cmd1" --port 8000 --server "cmd2" --port 5173 -- <command...>

Each --server is paired with the --port that follows it. Servers are killed
(whole process group) when the command finishes, succeeds or fails.
"""

import argparse
import os
import signal
import socket
import subprocess
import sys
import time

STARTUP_TIMEOUT_S = 60


def wait_for_port(port: int, timeout_s: float) -> bool:
    """Poll localhost:port until it accepts a TCP connection or timeout elapses."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--server", action="append", required=True, help="shell command")
    parser.add_argument("--port", action="append", type=int, required=True)

    if "--" not in sys.argv:
        parser.parse_args(sys.argv[1:])  # handles --help; otherwise fall through to the error
        print("error: missing '--' separator before the command to run", file=sys.stderr)
        return 2
    sep = sys.argv.index("--")
    own_args, command = sys.argv[1:sep], sys.argv[sep + 1 :]
    if not command:
        print("error: no command given after '--'", file=sys.stderr)
        return 2

    args = parser.parse_args(own_args)
    if len(args.server) != len(args.port):
        print("error: each --server needs a matching --port", file=sys.stderr)
        return 2

    procs: list[subprocess.Popen[bytes]] = []
    try:
        for cmd, port in zip(args.server, args.port):
            print(f"[with_server] starting: {cmd} (port {port})", file=sys.stderr)
            procs.append(subprocess.Popen(cmd, shell=True, start_new_session=True))
            if not wait_for_port(port, STARTUP_TIMEOUT_S):
                print(f"[with_server] port {port} never came up", file=sys.stderr)
                return 1
            print(f"[with_server] port {port} ready", file=sys.stderr)
        return subprocess.run(command).returncode
    finally:
        for proc in procs:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass


if __name__ == "__main__":
    sys.exit(main())
