Param(
  [string]$image,
  [string]$ip,
  [string]$user,
  [string]$pswd
)

# OpenBMC console commands to do different things
$turnHostPowerOff = "busctl set-property  xyz.openbmc_project.State.Chassis /xyz/openbmc_project/state/chassis0 xyz.openbmc_project.State.Chassis RequestedPowerTransition s xyz.openbmc_project.State.Chassis.Transition.Off"
$turnHostPowerOn  = "busctl set-property  xyz.openbmc_project.State.Host /xyz/openbmc_project/state/host0 xyz.openbmc_project.State.Host RequestedHostTransition s xyz.openbmc_project.State.Host.Transition.On"
$flashBiosImage   = "flashcp -v /tmp/bios.rom /dev/mtd/by-name/host-prime && dd if=/tmp/bios.rom of=/dev/mtd/by-name/vrom-prime"

# Use OpenBMC Console to force the remote host power off
plink -batch -ssh ${user}@${ip} -pw $pswd  "${turnHostPowerOff}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Unable to turn off host power!"
    exit 1
}

# Transfer BIOS image to the OpenBMC
pscp -pw ${pswd} ${image} ${user}@${ip}:/tmp/bios.rom
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Unable to transfer BIOS image!"
    exit 2
}

# Use OpenBMC Console to FLASH the image
plink -batch -ssh ${user}@${ip} -pw $pswd  "${flashBiosImage}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Unable to flash BIOS image!"
    exit 3
}

# Use open BMC console to turn on host power
plink -batch -ssh ${user}@${ip} -pw $pswd  "${turnHostPowerOn}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Unable to turn on host power image!"
    exit 4
}

Write-Host "SUCCESS: BIOS image transferred and flashed!"
