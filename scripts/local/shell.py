#!/usr/bin/env python3

import json
import shlex
import sys
import time
from cmd import Cmd
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final
from uuid import uuid4


BASE_DIR: Final[Path] = Path(__file__).resolve().parents[2]
LIVE: Final[Path] = BASE_DIR / "live"
DEFAULT_TIMEOUT_S = 30.0
POLL_INTERVAL_S = 0.1
TEXT_ENCODING = "utf-8"


def _normalize_newlines(value: Any) -> str:
    return str(value).replace("\r\n", "\n").replace("\r", "\n")


class SyncExecClient:
    def __init__(self, live_dir: Path = LIVE):
        self.live_dir = live_dir
        self.queued_dir = live_dir / "queued"
        self.completed_dir = live_dir / "completed"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.live_dir.mkdir(parents=True, exist_ok=True)
        self.queued_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _new_request_id() -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        return f"{ts}-{uuid4().hex[:8]}"

    def run_exec(self, interpreter: str, command: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> str:
        request_id = self._new_request_id()
        payload = {
            "class_name": "Exec",
            "interpreter": interpreter,
            "command": command,
        }

        out_path = self.queued_dir / f"{request_id}-out.txt"
        in_path = self.completed_dir / f"{request_id}-in.txt"
        out_path.write_text(json.dumps(payload, separators=(",", ":")), encoding=TEXT_ENCODING)

        deadline = time.time() + max(0.0, timeout_s)
        while True:
            if in_path.exists():
                body = _normalize_newlines(in_path.read_text(encoding=TEXT_ENCODING, errors="replace")).rstrip()
                return (body + "\n") if body else ""
            if time.time() >= deadline:
                raise TimeoutError(f"timed out ({timeout_s:.1f}s)")
            time.sleep(POLL_INTERVAL_S)


class CommandModule:
    usage = ""

    def __init__(self, client: SyncExecClient):
        self.client = client

    @staticmethod
    def _split_args(arg: str) -> list[str]:
        try:
            return shlex.split(arg)
        except ValueError as error:
            raise ValueError(f"invalid arguments: {error}") from error

    @staticmethod
    def parse_timeout(parts: list[str]) -> tuple[float, list[str]]:
        timeout = DEFAULT_TIMEOUT_S
        if parts and parts[0] == "--timeout":
            if len(parts) < 3:
                raise ValueError("usage: <command> [--timeout S] ...")
            try:
                timeout = float(parts[1])
            except ValueError as error:
                raise ValueError("--timeout must be a number") from error
            if timeout < 0:
                raise ValueError("--timeout must be >= 0")
            parts = parts[2:]
        return timeout, parts

    def run(self, arg: str) -> str:
        raise NotImplementedError


class ExecModule(CommandModule):
    usage = "exec [--timeout S] <powershell|bash|cmd> <command...>"

    def run(self, arg: str) -> str:
        parts = self._split_args(arg)
        if not parts:
            raise ValueError(f"usage: {self.usage}")

        timeout, parts = self.parse_timeout(parts)
        if len(parts) < 2:
            raise ValueError(f"usage: {self.usage}")

        interpreter = parts[0]
        command = shlex.join(parts[1:])
        return self.client.run_exec(interpreter=interpreter, command=command, timeout_s=timeout)


class FileModule(CommandModule):
    usage = "script [--timeout S] <powershell|bash|cmd> <local_file>"

    def run(self, arg: str) -> str:
        parts = self._split_args(arg)
        if not parts:
            raise ValueError(f"usage: {self.usage}")

        timeout, parts = self.parse_timeout(parts)
        if len(parts) != 2:
            raise ValueError(f"usage: {self.usage}")

        interpreter = parts[0]
        file_path = Path(parts[1]).expanduser()
        if not file_path.is_file():
            raise ValueError(f"file not found: {file_path}")

        command = file_path.read_text(encoding=TEXT_ENCODING, errors="replace")
        if not command.strip():
            raise ValueError(f"file is empty: {file_path}")

        return self.client.run_exec(interpreter=interpreter, command=command, timeout_s=timeout)


class Shell(Cmd):
    intro = "[void c2]"
    prompt = "c2> "

    def __init__(self, client: SyncExecClient | None = None):
        super().__init__()
        self.client = client or SyncExecClient()
        self.modules: dict[str, CommandModule] = {
            "exec": ExecModule(self.client),
            "script": FileModule(self.client),
        }
        self.intro = self._build_intro()

    def _build_intro(self) -> str:
        lines = ["[void c2]", ""]
        lines.extend(self.modules[name].usage for name in sorted(self.modules))
        return "\n".join(lines)

    def _run_module(self, name: str, arg: str) -> None:
        module = self.modules[name]
        print("...", flush=True)
        output = module.run(arg)
        print(output, end="")

    def _execute(self, name: str, arg: str) -> None:
        try:
            self._run_module(name, arg)
        except TimeoutError as error:
            print(f"error: {error}", file=sys.stderr)
        except ValueError as error:
            print(error, file=sys.stderr)

    def do_exec(self, arg: str):
        "Run an inline command on the remote host."
        self._execute("exec", arg)

    def do_script(self, arg: str):
        "Run a local script file on the remote host."
        self._execute("script", arg)

    def do_exit(self, _arg: str):
        return True

    def do_EOF(self, _arg: str):
        print()
        return True

    def default(self, line: str):
        print(f"unknown command: {line}", file=sys.stderr)

    def run_oneshot(self, argv: list[str]) -> None:
        if not argv:
            raise ValueError("no args specified")
        cmd_name = argv[0]
        if cmd_name not in self.modules:
            raise ValueError(f"unknown command: {' '.join(argv)}")
        self._execute(cmd_name, shlex.join(argv[1:]))


def main() -> None:
    shell = Shell()
    args = sys.argv[1:]
    if not args:
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print()
        return
    try:
        shell.run_oneshot(args)
    except ValueError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
