# LeRobot Metrics Dashboard (Streamlit)

This project tracks weekly snapshots of:

- LeRobot GitHub stars (`huggingface/lerobot`)
- Hugging Face LeRobot dataset count
- Unique uploaders of those LeRobot datasets
- GitHub repo count for `topic:robotics`
- GitHub repo count for `topic:lerobot`

It stores snapshots in `data/weekly_snapshots.csv` and visualizes trends in Streamlit.

## 1) Create a GitHub repository

1. In GitHub, click **New repository**.
2. Name it something like `LeRobot_Metrics`.
3. Keep it public or private (either is fine).
4. Create repository.

## 2) Put this project in your local folder

If you already have this folder, just run these commands from inside it:

```bash
git init
git add .
git commit -m "Initial LeRobot metrics dashboard"
```

Then connect your GitHub remote:

```bash
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

## 3) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4) (Optional but recommended) Create a GitHub token for local runs

1. GitHub -> **Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)** -> **Generate new token**.
2. Set scope: `public_repo` is enough for public repo reads; `repo` also works.
3. Copy token.

Set it in your terminal:

```bash
export GITHUB_TOKEN="ghp_xxx"
```

## 5) (Optional) Create a Hugging Face token

1. Hugging Face -> **Settings** -> **Access Tokens** -> **New token** (read).
2. Copy token.

Set it in your terminal:

```bash
export HF_TOKEN="hf_xxx"
```

## 6) Run first snapshot locally

```bash
python scripts/fetch_snapshot.py
```

You should see printed metrics and a new row appended to `data/weekly_snapshots.csv`.

## 7) Start dashboard locally

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## 8) Enable weekly automation in GitHub Actions

The workflow file is already included: `.github/workflows/weekly_snapshot.yml`.

It runs:

- Every Monday at 09:00 UTC
- On manual trigger (`workflow_dispatch`)

### Add HF token secret to GitHub

1. Open your repo on GitHub.
2. **Settings** -> **Secrets and variables** -> **Actions**.
3. Click **New repository secret**.
4. Name: `HF_TOKEN`
5. Value: your `hf_xxx` token.

`GITHUB_TOKEN` is automatic in GitHub Actions and is already used by the workflow.

## 9) Manually trigger first workflow run

1. GitHub repo -> **Actions** tab.
2. Select **Weekly LeRobot Snapshot** workflow.
3. Click **Run workflow** -> **Run workflow**.
4. Wait for success.

The workflow will commit a new row to `data/weekly_snapshots.csv`.

## 10) Keep dashboard updated

Whenever new snapshots are committed, pull latest and run Streamlit:

```bash
git pull
source .venv/bin/activate
streamlit run app.py
```

## File layout

- `scripts/fetch_snapshot.py`: fetches API metrics and appends CSV snapshot
- `data/weekly_snapshots.csv`: historical snapshots
- `app.py`: Streamlit dashboard
- `.github/workflows/weekly_snapshot.yml`: weekly automation
