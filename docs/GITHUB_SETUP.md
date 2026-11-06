# Publish Week 1 documentation to the existing Urielle research repository

**Target:** https://github.com/wholidi/Urielle-AIMS-Audit-Reliability

The repository already contains a `README.md`. Do **not** initialize a new Git repository in the full OdySEA research workspace, and do **not** push to the Urielle production toolkit.

1. Extract this package to a clean local working directory.
2. In PowerShell, clone the existing research repository and copy the inspected files into that clone:

```powershell
$repo = Join-Path (Get-Location) "Urielle-AIMS-Audit-Reliability"
git clone https://github.com/wholidi/Urielle-AIMS-Audit-Reliability.git $repo
cd $repo
# Copy the inspected public package contents here.
git status --short
git diff -- README.md
git add -- README.md .gitignore benchmark docs src tests validation
git diff --cached --name-only
git commit -m "docs: publish Week 1 technical evidence and controls"
git push origin main
```

Never copy or stage `P1C_Restricted_Admin`, reviewer calibration CSVs, restricted labels, case mappings or the entire local benchmark workspace. Review all staged files before committing. If your clone path already exists, do not overwrite it; open the existing clone instead.
