# Publish Week 1 documentation to the existing Urielle research repository

**Target:** https://github.com/wholidi/Urielle-AIMS-Audit-Reliability

The repository already contains a `README.md`. Do **not** initialize a new Git repository in the full OdySEA research workspace, and do **not** push to the Urielle production toolkit.

1. Extract this package to a clean location such as `C:\AI Project\Urielle_AIMS_Audit_Reliability_Public_Package`.
2. In PowerShell, clone the existing research repository and copy the inspected files into that clone:

```powershell
$repo = "C:\AI Project\Urielle_AIMS_Audit_Reliability_Public"
git clone https://github.com/wholidi/Urielle-AIMS-Audit-Reliability.git $repo
cd $repo
# Copy the contents of the extracted package (README.md, .gitignore, docs/) here.
git status --short
git diff -- README.md
git add README.md .gitignore docs/METHODOLOGY.md docs/WEEK1_CLOSURE.md docs/WEEK2_MVP1_PLAN.md docs/GITHUB_SETUP.md
git diff --cached --name-only
git commit -m "docs: close Week 1 Urielle AIMS audit reliability milestone"
git push origin main
```

Never copy or stage `P1C_Restricted_Admin`, reviewer calibration CSVs, restricted labels, case mappings or the entire local benchmark workspace. Review all staged files before committing. If your clone path already exists, do not overwrite it; open the existing clone instead.
