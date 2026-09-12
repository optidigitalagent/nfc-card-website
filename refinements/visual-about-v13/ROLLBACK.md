# Rollback to the accepted v12 application

Recovery is local and file-scoped. It does not roll back PostgreSQL, orders, reviews, uploads, credentials or external services; v13 did not migrate or change those systems.

1. Preserve any edits made after this v13 acceptance. The rollback helper refuses to overwrite a file whose current digest differs from the final v13 inventory.
2. From the existing NFC application directory, run a verification-only dry run:

```powershell
[REDACTED_LOCAL_PATH] -X utf8 refinements/visual-about-v13/restore_v12.py
```

3. When rollback is intended, repeat with `--apply`. It restores modified existing files from the checksum-verified `baseline/recovery.zip` and deletes only exact byte-verified v13 additions listed in `files-changed.json`. There is no recursive directory deletion. The task evidence and all private data remain untouched.
4. The existing preview reads the restored generated HTML/assets per request. Reload `http://127.0.0.1:8765/`. If the preview is stopped, start the existing `Start-Commerce-Preview.ps1` helper. No new site or process stack is needed. Do not run the old builder into historical acceptance evidence merely to restore HTML already present in the snapshot.
5. Confirm the recovered source/public digests against `RECOVERY_SNAPSHOT.json`, open the standard/branded product and order pages, and verify that the accepted zero-review behavior remains. No database rollback or production operation is required.

Archive SHA-256: `eb27c8544287783c8759566cfcac1585ba59ad0108dae5cb6c23cc37fc1a24b5`. Exact recovery and changed-file manifests are linked in [RECOVERY_SNAPSHOT.json](RECOVERY_SNAPSHOT.json) and [files-changed.json](files-changed.json). The apply operation has not been run during refinement acceptance.
