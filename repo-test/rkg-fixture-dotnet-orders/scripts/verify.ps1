$ErrorActionPreference = "Stop"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    python scripts/validate-inventory.py
    if ($LASTEXITCODE -ne 0) { throw "Inventory validation failed" }
    dotnet restore Orders.slnx --locked-mode
    if ($LASTEXITCODE -ne 0) { throw "Restore failed" }
    dotnet build Orders.slnx --no-restore --configuration Release
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    dotnet test Orders.slnx --no-build --no-restore --configuration Release
    if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
} finally { Pop-Location }
