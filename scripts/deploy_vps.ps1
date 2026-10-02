param(
  [string]$HostAlias = "bmv-neuro-lab",
  [switch]$IncludeData
)
$ErrorActionPreference="Stop"
$Root=(Resolve-Path "$PSScriptRoot\..").Path
$Bundle=Join-Path $Root "artifacts\options-system-vps.tar.gz"
$Items=@("src","scripts","tests","docs","deploy","artifacts","requirements-dev.txt","README.md")
if($IncludeData){$Items += @("data\raw\prospective","data\processed")}

Push-Location $Root
try {
  if(Test-Path $Bundle){Remove-Item $Bundle -Force}
  tar -czf $Bundle --exclude=.env --exclude=.venv --exclude='__pycache__' @Items
  scp $Bundle "${HostAlias}:/home/ljamtz/options-system-vps.tar.gz"
  ssh $HostAlias "mkdir -p /home/ljamtz/options-system && tar -xzf /home/ljamtz/options-system-vps.tar.gz -C /home/ljamtz/options-system && rm /home/ljamtz/options-system-vps.tar.gz"
  Write-Output "UPLOAD_OK"
  Write-Output "Next: ensure /home/ljamtz/options-system/.env exists, then run deploy/scripts/install_vps.sh"
} finally { Pop-Location }
