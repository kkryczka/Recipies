param(
    [switch]$CreateGitHubRepo
)

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is not installed or not on PATH. Please install Git and re-run this script."
    exit 1
}

git init -b main
git add .
git commit -m "Initial commit: scaffold FastAPI recipe app"

if ($CreateGitHubRepo) {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        Write-Error "GitHub CLI (gh) not found. Install it or create the repo manually."
        exit 1
    }
    $repoName = Split-Path -Leaf (Get-Location)
    gh repo create $repoName --public --source=. --remote=origin --push
}

Write-Host "Repository initialized locally."