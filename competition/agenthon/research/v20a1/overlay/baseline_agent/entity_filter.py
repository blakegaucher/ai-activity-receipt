"""Source-only v20a manifest identity admissibility guard.

DO NOT treat deterministic admissibility as judge-rated entailment.
Manifest label matching is the official scorer's declared rule; no CIK
heuristics, date inference or external information are permitted.
"""
from __future__ import annotations
import json
from pathlib import Path
from .indexer import IndexedDoc


class IdentityManifestError(ValueError):
    pass


def load_manifest_labels(corpus_dir: str | Path, docs: list[IndexedDoc], *,
                         manifest_ref: str | None = None) -> dict[str, dict]:
    corpus_dir = Path(corpus_dir)
    unit_dir = corpus_dir.parent
    # The task is the authority: worked exemplar declares "manifest.json" at /input,
    # public practice units declare "corpus/manifest.json" at /input/corpus.
    ref = manifest_ref if manifest_ref is not None else "corpus/manifest.json"
    if not isinstance(ref, str) or ref not in ("manifest.json", "corpus/manifest.json"):
        raise IdentityManifestError("unsafe/unsupported corpus manifest reference")
    path = unit_dir / ref
    if not path.is_file() or path.is_symlink():
        raise IdentityManifestError("declared frozen corpus manifest unavailable")
    manifest=json.loads(path.read_text(encoding="utf-8"))
    files=manifest.get("files")
    if not isinstance(files,list):
        raise IdentityManifestError("invalid manifest files list")
    labels={}
    for entry in files:
        if not isinstance(entry,dict) or entry.get("role")!="corpus":
            continue
        path_label=entry.get("path")
        if not isinstance(path_label,str) or not path_label.startswith("corpus/"):
            raise IdentityManifestError("unexpected corpus path in manifest")
        docid=Path(path_label).stem
        ids=entry.get("entity_ids")
        shared=entry.get("shared",False)
        if ids is not None and (not isinstance(ids,list) or not all(isinstance(v,str) for v in ids)):
            raise IdentityManifestError("invalid entity_ids")
        if type(shared) is not bool:
            raise IdentityManifestError("invalid shared flag")
        if ids is None and not shared:
            raise IdentityManifestError("manifest entry has no identity attribution")
        if docid in labels:
            raise IdentityManifestError("duplicate document identity")
        labels[docid]={"entity_ids":ids or [],"shared":shared}
    docids=[d.doc_id for d in docs]
    if len(set(docids))!=len(docids) or set(labels)!=set(docids):
        raise IdentityManifestError("manifest/corpus document mismatch")
    return labels


def admissible_docs(docs: list[IndexedDoc], labels: dict[str,dict], entity_id: str) -> list[IndexedDoc]:
    if not isinstance(entity_id,str) or not entity_id:
        raise IdentityManifestError("missing entity_id")
    return [d for d in docs if d.doc_id in labels and
            (entity_id in labels[d.doc_id]["entity_ids"] or labels[d.doc_id]["shared"])]
