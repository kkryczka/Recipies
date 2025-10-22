# Run the Recipies app using Anaconda/conda if available.
$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
$envName = 'recipies'

$condaCmd = Get-Command conda -ErrorAction SilentlyContinue
if ($null -ne $condaCmd) {
    Write-Host "conda found. Checking for environment '$envName'..."
    $found = conda env list | Select-String -Pattern "^\s*$envName\s" -Quiet
    if (-not $found) {
        Write-Host "Environment '$envName' not found. Creating from environment.yml..."
        conda env create -f environment.yml
    } else {
        Write-Host "Environment '$envName' exists."
    }
    Write-Host "Running app in environment '$envName'..."
    conda run -n $envName --no-capture-output python .\src\main.py
    exit $LASTEXITCODE
} else {
    Write-Host "conda not found on PATH. Please open the Anaconda Prompt and run the following commands:"
    Write-Host "  conda env create -f environment.yml"
    Write-Host "  conda activate $envName"
    Write-Host "  python .\src\main.py"
    exit 1
}
