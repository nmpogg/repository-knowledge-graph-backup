#!/usr/bin/env sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 scripts/validate-inventory.py
dotnet restore Orders.slnx --locked-mode
dotnet build Orders.slnx --no-restore --configuration Release
dotnet test Orders.slnx --no-build --no-restore --configuration Release
