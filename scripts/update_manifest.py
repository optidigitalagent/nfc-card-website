"""Refresh the release manifest only after all source edits and validation finish."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_manifest import (ROOT, MANIFEST, HANDOFF_MANIFEST, HANDOFF_MANIFEST_SHA256,
                             ManifestError, read_regular, release_provenance, source_files, verify)
from release_guard import guard


def refresh(root: Path = ROOT) -> int:
    files = source_files(root)
    if HANDOFF_MANIFEST not in files or hashlib.sha256(read_regular(files[HANDOFF_MANIFEST])).hexdigest() != HANDOFF_MANIFEST_SHA256:
        raise ManifestError("Preserve the original handoff manifest byte-for-byte before refresh")
    findings = guard(root)
    if findings:
        raise ManifestError(f"Release guard rejected refresh ({len(findings)} findings); run scripts/release_guard.py")
    entries = []
    for name, path in sorted(files.items()):
        if name != MANIFEST:
            data = read_regular(path)
            entries.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    result = {"algorithm": "SHA-256", "manifest_self_excluded": "Self-hashing is circular; Git commit/release archive seals this manifest.",
              "file_count_including_manifest": len(entries) + 1, "release_source": release_provenance(), "files": entries}
    # Detect edits made during this scan; callers must still stop concurrent writers.
    again = source_files(root)
    if again.keys() != files.keys() or any(hashlib.sha256(read_regular(again[i["path"]])).hexdigest() != i["sha256"] for i in entries):
        raise ManifestError("Source changed during refresh; stop concurrent edits and retry")
    target = Path(root) / MANIFEST
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    # Publish complete bytes atomically; an interrupted write preserves the old
    # manifest. Temporary files are siblings, not a broad ignored source root.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=".manifest-refresh-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return verify(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        count = refresh(args.root)
    except (ManifestError, OSError) as exc:
        print("Manifest refresh failed: " + (str(exc) if isinstance(exc, ManifestError) else "unreadable source file"))
        return 1
    print(f"Manifest refreshed and verified: {count} hashed files plus manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
