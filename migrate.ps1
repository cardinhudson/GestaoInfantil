Param(
    [string]$Db = $env:GESTAO_DB
)
Write-Host "Running DB migration (init_db)..."
if ($Db) { Write-Host "Using GESTAO_DB=$Db" }
python -c "from db import init_db; init_db()"
Write-Host "Migration complete."
