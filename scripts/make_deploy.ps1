param(
    [string]$DeployPath = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $DeployPath) {
    $DeployPath = Join-Path $ProjectRoot "deploy_package"
}

$DeployParent = Split-Path $DeployPath -Parent
if ($DeployParent -and -not (Test-Path $DeployParent)) {
    New-Item -ItemType Directory -Path $DeployParent | Out-Null
}

if (Test-Path $DeployPath) {
    Remove-Item -LiteralPath $DeployPath -Recurse -Force
}
New-Item -ItemType Directory -Path $DeployPath | Out-Null

$files = @(
    "main.py",
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "README.md"
)

foreach ($file in $files) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $file) -Destination (Join-Path $DeployPath $file)
}

$directories = @(
    "src",
    "tests",
    "docs",
    "scripts"
)

foreach ($directory in $directories) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $directory) -Destination (Join-Path $DeployPath $directory) -Recurse
}

$excludedNames = @(
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache"
)

Get-ChildItem -LiteralPath $DeployPath -Recurse -Force -Directory |
    Where-Object { $excludedNames -contains $_.Name } |
    Sort-Object FullName -Descending |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }

Get-ChildItem -LiteralPath $DeployPath -Recurse -Force -File |
    Where-Object { $_.Extension -eq ".pyc" -or $_.Extension -eq ".pyo" } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }

New-Item -ItemType Directory -Path (Join-Path $DeployPath "logs") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $DeployPath "output") | Out-Null
New-Item -ItemType File -Path (Join-Path $DeployPath "logs\.gitkeep") | Out-Null
New-Item -ItemType File -Path (Join-Path $DeployPath "output\.gitkeep") | Out-Null

Write-Host "Deploy folder generated:"
Write-Host $DeployPath
