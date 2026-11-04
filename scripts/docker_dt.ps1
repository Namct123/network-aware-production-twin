param(
    [ValidateSet('build','demo','fault','strict','tests','acceptance','predictive-check','measured-check','observer-check','reconfiguration-check','robustness-check','adaptive-check','recovery-check','reset-check','integration-check','qualification-check','physics-check','background-check','boundary-study','stream-check','stream-archive-check','predictive-replay-study','software-check','manifest')]
    [string]$Mode = 'demo',
    [string]$Config = '',
    [string]$Plan = '',
    [string]$ResetSettings = '',
    [ValidateRange(1,6)][int]$Bin = 1,
    [ValidatePattern('^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$')]
    [string]$Tag = 'accepted-20261103-software-v2'
)
if ($Mode -eq 'build' -and -not $PSBoundParameters.ContainsKey('Tag')) {
    $Tag = 'candidate-20261104-mujoco-only'
}
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$dockerArgs = switch ($Mode) {
    'build' { @('compose','build','dt') }
    'tests' { @('compose','run','--rm','--entrypoint','python','dt','-m','unittest','discover','-s','mujoco','-p','test_*.py') }
    'manifest' { @('compose','run','--rm','--entrypoint','cat','dt','/app/source_manifest.json') }
    default { @('compose','run','--rm','dt',$Mode) }
}
if ($Mode -in @('demo','fault','strict')) { $dockerArgs += @('--bin', "$Bin") }
if ($Config) {
    if ($Mode -notin @('demo','fault','strict','acceptance','predictive-check','measured-check','observer-check','reconfiguration-check','robustness-check','adaptive-check','recovery-check','reset-check','qualification-check','physics-check','background-check','boundary-study','predictive-replay-study')) {
        throw '-Config applies only to simulation modes.'
    }
    # Config is a filename under the read-only mounted profile directory.
    if ([IO.Path]::GetFileName($Config) -ne $Config -or $Config -match '[/\\:]') {
        throw 'Use only the filename of a JSON profile in mujoco/configs.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot "mujoco/configs/$Config") -PathType Leaf)) {
        throw "Missing profile: $Config"
    }
    $dockerArgs += @('--config', "/profiles/$Config")
}
if ($Plan) {
    if ($Mode -notin @('robustness-check','adaptive-check','qualification-check','boundary-study','predictive-replay-study')) { throw '-Plan requires robustness-check, adaptive-check, qualification-check or boundary-study.' }
    if ([IO.Path]::GetFileName($Plan) -ne $Plan -or $Plan -match '[/\\:]') {
        throw 'Use only a plan filename under mujoco/experiments.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot "mujoco/experiments/$Plan") -PathType Leaf)) {
        throw "Missing experiment plan: $Plan"
    }
    $dockerArgs += @('--plan', "/plans/$Plan")
}
if ($ResetSettings) {
    if ($Mode -ne 'reset-check') { throw '-ResetSettings requires reset-check.' }
    if ([IO.Path]::GetFileName($ResetSettings) -ne $ResetSettings -or $ResetSettings -match '[/\\:]') {
        throw 'Use only a settings filename under mujoco/experiments.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot "mujoco/experiments/$ResetSettings") -PathType Leaf)) {
        throw "Missing reset settings: $ResetSettings"
    }
    $dockerArgs += @('--settings', "/plans/$ResetSettings")
}
Push-Location $projectRoot
$previousImageTag = $env:DT_IMAGE_TAG
try {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $env:DT_IMAGE_TAG = $Tag
        if ($Mode -eq 'build') {
            if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 docker/build_image.py --tag $Tag }
            else { & python docker/build_image.py --tag $Tag }
        } else { & docker @dockerArgs }
    } else {
        # Existing machine uses Docker Engine in WSL, with no Docker Desktop.
        $linuxRoot = '/mnt/' + $projectRoot.Substring(0,1).ToLowerInvariant() + $projectRoot.Substring(2).Replace('\','/')
        if ($Mode -eq 'build') {
            & wsl.exe -d Ubuntu-24.04 -u root --cd $linuxRoot -- python3 docker/build_image.py --tag $Tag
        } else { & wsl.exe -d Ubuntu-24.04 -u root --cd $linuxRoot -- env "DT_IMAGE_TAG=$Tag" docker @dockerArgs }
    }
    $result = $LASTEXITCODE
} finally {
    $env:DT_IMAGE_TAG = $previousImageTag
    Pop-Location
}
exit $result
