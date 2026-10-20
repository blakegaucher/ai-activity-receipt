"""Agenthon T4 v20a.2 source-only manifest identity hardening.

This is a new unmerged review-only candidate. Admissible does not mean entailed.
Reject invalid, untrusted or mismatched manifest and corpus evidence before retrieval.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import stat
from pathlib import Path
from .indexer import IndexedDoc

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_ALLOWED_MANIFESTS = frozenset(("manifest.json", "corpus/manifest.json"))
_MAX_DOC_BYTES = 8 * 1024 * 1024


class IdentityManifestError(ValueError):
    pass


def _valid_date(value: str | None) -> bool:
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def load_manifest_labels(
    corpus_dir: str | Path,
    docs: list[IndexedDoc],
    *,
    manifest_ref: str | None = None,
) -> dict[str, dict]:
    corpus_dir = Path(corpus_dir)
    unit_dir = corpus_dir.parent
    # Only the two declared paths in the pinned public Track 4 contract are supported.
    ref = manifest_ref if manifest_ref is not None else "corpus/manifest.json"
    if not isinstance(ref, str) or ref not in _ALLOWED_MANIFESTS:
        raise IdentityManifestError("invalid task-declared corpus manifest path")
    manifest_path = unit_dir / ref
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise IdentityManifestError("frozen manifest not available as regular file")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise IdentityManifestError("manifest unreadable") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise IdentityManifestError("manifest files[] missing")

    # Scorer's corpus doc IDs come from 'corpus/<doc_id>.json', not a free-form
    # doc_id property in a JSON payload. The baseline indexer currently permits
    # that property; ensure it cannot silently change which document is cited.
    by_id: dict[str, dict] = {}
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or entry.get("role") != "corpus":
            continue
        name = entry.get("path")
        if name == "corpus/manifest.json":
            continue  # corpus index, never a citation target
        if not isinstance(name, str) or not name.startswith("corpus/"):
            raise IdentityManifestError("noncanonical corpus path")
        filename = name[7:]
        if not filename.endswith(".json") or not _ID.fullmatch(filename[:-5]):
            raise IdentityManifestError("invalid corpus document identifier")
        did = filename[:-5]
        if did == "task" or did == "manifest" or did in by_id:
            raise IdentityManifestError("duplicate or reserved corpus document identifier")
        sha = entry.get("sha256")
        if not isinstance(sha, str) or not _DIGEST.fullmatch(sha):
            raise IdentityManifestError("unverifiable corpus document")
        ids = entry.get("entity_ids")
        shared = entry.get("shared")
        if shared is not None and shared is not True:
            raise IdentityManifestError("shared must be true if present")
        if ids is not None:
            if not isinstance(ids, list) or any(not isinstance(x, str) or not x for x in ids):
                raise IdentityManifestError("invalid entity_ids")
            if len(set(ids)) != len(ids):
                raise IdentityManifestError("duplicate entity_ids")
        if shared is True and ids:
            raise IdentityManifestError("shared corpus document also entity-labelled")
        if ids is None and shared is not True:
            raise IdentityManifestError("unlabelled evidence document")
        by_id[did] = {"entity_ids":ids or [], "shared":shared is True, "sha256":sha}

    ids = [x.doc_id for x in docs]
    if len(ids) != len(set(ids)) or set(ids) != set(by_id):
        raise IdentityManifestError("manifest and indexed corpus doc IDs differ")

    for doc in docs:
        if not _valid_date(doc.doc_date):
            raise IdentityManifestError("corpus document date is absent or noncanonical")
        file_path = corpus_dir / (doc.doc_id + ".json")
        if file_path.is_symlink() or not file_path.is_file():
            raise IdentityManifestError("corpus document missing or is symlink")
        if not stat.S_ISREG(file_path.stat().st_mode):
            raise IdentityManifestError("corpus document not regular file")
        raw = file_path.read_bytes()
        if len(raw) > _MAX_DOC_BYTES or hashlib.sha256(raw).hexdigest() != by_id[doc.doc_id]["sha256"]:
            raise IdentityManifestError("corpus file checksum or size invalid")
        # The baseline indexer uses payload doc_id if available; the scorer
        # always derives it from manifest name. Require agreement.
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise IdentityManifestError("corpus document JSON malformed") from exc
        if not isinstance(payload, dict) or payload.get("doc_id",doc.doc_id) != doc.doc_id:
            raise IdentityManifestError("corpus payload doc ID disagrees with trusted path")
        if payload.get("doc_date") != doc.doc_date:
            raise IdentityManifestError("indexed corpus date disagrees with verified document")
    return {key:{"entity_ids":x["entity_ids"],"shared":x["shared"]} for key,x in by_id.items()}


def admissible_docs(docs: list[IndexedDoc], labels: dict[str,dict], entity_id: str) -> list[IndexedDoc]:
    if not isinstance(entity_id,str) or not entity_id:
        raise IdentityManifestError("missing entity_id")
    return [
        d for d in docs
        if d.doc_id in labels and (
            entity_id in labels[d.doc_id]["entity_ids"] or labels[d.doc_id]["shared"]
        )
    ]

