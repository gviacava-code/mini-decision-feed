Remove-Item -Recurse -Force lambda_package -ErrorAction SilentlyContinue
Remove-Item -Force lambda_package.zip -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path lambda_package | Out-Null

pip install fastapi mangum pydantic anthropic duckdb python-dotenv numpy pandas `
  --target lambda_package `
  --upgrade `
  --quiet `
  --platform manylinux2014_x86_64 `
  --implementation cp `
  --python-version 3.12 `
  --only-binary=:all:

Copy-Item deployment\lambda_handler.py lambda_package\lambda_handler.py
Copy-Item -Recurse api lambda_package\api
New-Item -ItemType Directory -Path lambda_package\data | Out-Null
Copy-Item data\sales.duckdb lambda_package\data\sales.duckdb

Add-Type -Assembly "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Resolve-Path "lambda_package").Path,
    (Join-Path (Resolve-Path ".").Path "lambda_package.zip")
)

Write-Host "Done:" ([math]::Round((Get-Item lambda_package.zip).length/1MB, 1)) "MB" -ForegroundColor Green