#!/usr/bin/env python3
print("Hello World")

from subprocess import Popen as O, PIPE as P
def exec(command:list): return "\n".join(list(map(lambda _: _.decode("utf-8"), O(command, stdout=P, stderr=P).communicate())))
print(exec(["powershell", "-c", "whoami"]))