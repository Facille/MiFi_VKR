param(
    [string]$Output = "vkr_code_context_predictor_release.zip"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$destination = Join-Path $root $Output
$staging = Join-Path $env:TEMP ("code_context_predictor_release_" + [guid]::NewGuid().ToString("N"))

$excludedDirs = @(
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "build",
    "dist"
)

$excludedExtensions = @(".pyc", ".pyo")
$excludedNames = @($Output)

function Copy-CleanDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Target
    )

    New-Item -ItemType Directory -Force -Path $Target | Out-Null

    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        if ($_.PSIsContainer -and $excludedDirs -contains $_.Name) {
            return
        }
        if (-not $_.PSIsContainer -and ($excludedExtensions -contains $_.Extension -or $excludedNames -contains $_.Name)) {
            return
        }

        $childTarget = Join-Path $Target $_.Name
        if ($_.PSIsContainer) {
            Copy-CleanDirectory -Source $_.FullName -Target $childTarget
        } else {
            Copy-Item -LiteralPath $_.FullName -Destination $childTarget
        }
    }
}

New-Item -ItemType Directory -Force -Path $staging | Out-Null

Get-ChildItem -LiteralPath $root -Force | ForEach-Object {
    $source = $_.FullName
    $target = Join-Path $staging $_.Name

    if ($_.PSIsContainer -and $excludedDirs -contains $_.Name) {
        return
    }

    if (-not $_.PSIsContainer -and ($excludedExtensions -contains $_.Extension -or $excludedNames -contains $_.Name)) {
        return
    }

    if ($_.PSIsContainer) {
        Copy-CleanDirectory -Source $source -Target $target
    } else {
        Copy-Item -LiteralPath $source -Destination $target
    }
}

if (Test-Path -LiteralPath $destination) {
    Remove-Item -LiteralPath $destination -Force
}

Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $destination -Force
Remove-Item -LiteralPath $staging -Recurse -Force

Write-Host "Created $destination"
