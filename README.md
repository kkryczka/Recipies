# Recipies

Small starter project for storing and loading recipes.

Files created:

Try it (PowerShell):

```powershell
python src/main.py
```

Web app (FastAPI + SQLite)

Run the web app using the `recipies` conda environment.

1. Create/update the conda environment and install dependencies:

```powershell
conda env update -f environment.yml
conda activate recipies
```

2. Run the development server:

```powershell
uvicorn src.app:app --reload
```

Then open http://127.0.0.1:8000 in your browser.

Which CI enhancements should I add next?

Git
---

To initialize a local git repository and push to GitHub (optional):

1. Run the helper script (requires Git locally):

```powershell
.\init-repo.ps1
# or to also create a GitHub repo with gh:
.\init-repo.ps1 -CreateGitHubRepo
```

If you prefer manual steps:

```powershell
git init -b main
git add .
git commit -m "Initial commit"
# then create a remote and push
git remote add origin <your-remote-url>
git push -u origin main
```


