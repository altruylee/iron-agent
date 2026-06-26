"""Route a task through low-token memory indexes before reading memory."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FALLBACK_INDEX = {
    "task review": {
        "tier": "hot",
        "aliases": ["复盘", "任务复盘", "review", "workflow"],
        "paths": [
            "workspace/memory/episodes/workflow/task-review/INDEX.md",
            "workspace/memory/semantic/sops/task-review.md",
        ],
    },
    "user registration": {
        "tier": "warm",
        "aliases": ["用户注册", "注册", "登录", "onboarding", "registration"],
        "paths": [
            "workspace/memory/episodes/user/registration/INDEX.md",
            "workspace/memory/semantic/sops/user-registration.md",
        ],
    },
    "development": {
        "tier": "hot",
        "aliases": ["开发", "代码", "bug", "测试", "repo", "code", "test", "refactor"],
        "paths": [
            "packs/domain-agents/INDEX.md",
            "workspace/memory/episodes/development/INDEX.md",
        ],
    },
}

SEMANTIC_INDEX_REL = "workspace/memory/semantic_index.jsonl"
SEMANTIC_VECTORS_REL = "workspace/memory/semantic_vectors.jsonl"
SEMANTIC_CACHE_REL = "workspace/meta/semantic-cache.json"
MAX_SUMMARY_CHARS = 520


def rel_path(value: str) -> Path:
    return Path(*value.replace("\\", "/").split("/"))


def normalize_entry(value: object) -> dict[str, object]:
    if isinstance(value, list):
        return {"paths": [str(path) for path in value], "aliases": [], "tier": "warm"}
    if isinstance(value, dict):
        paths = value.get("paths", [])
        aliases = value.get("aliases", [])
        return {
            "paths": [str(path) for path in paths] if isinstance(paths, list) else [],
            "aliases": [str(alias) for alias in aliases] if isinstance(aliases, list) else [],
            "tier": str(value.get("tier", "warm")),
        }
    return {"paths": [], "aliases": [], "tier": "warm"}


def load_index(root: Path) -> dict[str, dict[str, object]]:
    index_path = root / "workspace" / "memory" / "index.json"
    if not index_path.exists():
        return {topic: normalize_entry(value) for topic, value in FALLBACK_INDEX.items()}
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("workspace/memory/index.json must be an object")
    result: dict[str, dict[str, object]] = {}
    for topic, value in data.items():
        entry = normalize_entry(value)
        if entry["paths"]:
            result[str(topic)] = entry
    return result


def score_topic(task: str, topic: str, aliases: list[str] | None = None, tier: str = "warm") -> int:
    lowered = task.lower()
    score = 0
    if topic.lower() in lowered:
        score += 10
    for token in topic.lower().replace("-", " ").split():
        if token and token in lowered:
            score += 2
    for alias in aliases or []:
        alias_lower = alias.lower()
        if alias_lower and alias_lower in lowered:
            score += 8
        for token in alias_lower.replace("-", " ").split():
            if token and token in lowered:
                score += 2
    for char in topic:
        if "\u4e00" <= char <= "\u9fff" and char in task:
            score += 1
    matched = score > 0
    if matched and tier == "hot":
        score += 2
    elif matched and tier == "cold":
        score -= 2
    return score


def keyword_rank(root: Path, task: str, include_cold: bool = False) -> list[tuple[str, float, str]]:
    ranked: list[tuple[str, float, str]] = []
    for topic, entry in load_index(root).items():
        tier = str(entry.get("tier", "warm"))
        score = score_topic(task, topic, entry.get("aliases", []), tier)
        if score < 2:
            continue
        for item in entry.get("paths", []):
            normalized = str(item).replace("\\", "/")
            if not include_cold and ("/cold/" in normalized or tier == "cold"):
                continue
            if (root / rel_path(normalized)).exists():
                ranked.append((normalized, float(score) / 20.0, "keyword"))
    return sorted(ranked, key=lambda item: item[1], reverse=True)


def is_cjk(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9_-]{1,}", lowered)
    cjk = "".join(char for char in lowered if is_cjk(char))
    for size in (2, 3):
        tokens.extend(cjk[index : index + size] for index in range(max(0, len(cjk) - size + 1)))
    tokens.extend(char for char in cjk if char.strip())
    return [token for token in tokens if token]


def vectorize(text: str) -> dict[str, float]:
    counts: dict[str, float] = {}
    for token in tokenize(text):
        counts[token] = counts.get(token, 0.0) + 1.0
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {key: value / norm for key, value in counts.items()}


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def tier_for_path(rel: str) -> str:
    normalized = rel.replace("\\", "/")
    if "/hot/" in normalized:
        return "hot"
    if "/cold/" in normalized:
        return "cold"
    if "/warm/" in normalized:
        return "warm"
    if "/semantic/sops/" in normalized:
        return "hot"
    return "warm"


def type_for_path(rel: str) -> str:
    normalized = rel.replace("\\", "/")
    if "/semantic/sops/" in normalized:
        return "sop"
    if "/episodes/" in normalized:
        return "episode"
    if "/hot/" in normalized or "/warm/" in normalized or "/cold/" in normalized:
        return "route"
    return "memory"


def summarize_markdown(path: Path, rel: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    summary: list[str] = []
    for raw in text.splitlines():
        line = raw.strip().strip("|").strip()
        if not line or line == "---" or line.startswith("<!--"):
            continue
        if line.startswith("#"):
            summary.append(line.lstrip("#").strip())
        elif line.startswith("- "):
            summary.append(line[2:].strip())
        elif "|" in line and not set(line.replace("|", "").strip()) <= {"-", ":"}:
            summary.append(re.sub(r"\s*\|\s*", " ", line).strip())
        elif len(line) <= 160 and len(summary) < 3:
            summary.append(line)
        if len(" ".join(summary)) >= MAX_SUMMARY_CHARS:
            break
    path_words = " ".join(Path(rel).with_suffix("").parts)
    result = " ".join(dict.fromkeys([path_words, *summary]))
    return result[:MAX_SUMMARY_CHARS]


def iter_memory_leaf_files(root: Path) -> list[Path]:
    memory_root = root / "workspace" / "memory"
    if not memory_root.exists():
        return []
    files: list[Path] = []
    for path in memory_root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if path.name == "INDEX.md":
            continue
        if "/shadow-review/" in rel:
            continue
        files.append(path)
    return sorted(files)


def build_semantic_index(root: Path) -> dict[str, Any]:
    index_path = root / SEMANTIC_INDEX_REL
    vectors_path = root / SEMANTIC_VECTORS_REL
    cache_path = root / SEMANTIC_CACHE_REL
    cache: dict[str, Any] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}

    records: list[dict[str, Any]] = []
    vectors: list[dict[str, Any]] = []
    next_cache: dict[str, Any] = {}
    for path in iter_memory_leaf_files(root):
        stat = path.stat()
        rel = path.relative_to(root).as_posix()
        cached = cache.get(rel) if isinstance(cache.get(rel), dict) else {}
        if cached.get("mtime_ns") == stat.st_mtime_ns and cached.get("size") == stat.st_size:
            record = cached.get("record")
            vector = cached.get("vector")
        else:
            summary = summarize_markdown(path, rel)
            record = {
                "id": hashlib.sha1(rel.encode("utf-8")).hexdigest()[:16],
                "text": summary,
                "path": rel,
                "tier": tier_for_path(rel),
                "type": type_for_path(rel),
                "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
            }
            vector = vectorize(summary)
        if isinstance(record, dict) and isinstance(vector, dict):
            records.append(record)
            vectors.append({"id": record["id"], "path": rel, "vector": vector})
            next_cache[rel] = {
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
                "record": record,
                "vector": vector,
            }

    index_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records) + ("\n" if records else ""), encoding="utf-8")
    vectors_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in vectors) + ("\n" if vectors else ""), encoding="utf-8")
    cache_path.write_text(json.dumps(next_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"records": len(records), "index": index_path.relative_to(root).as_posix(), "vectors": vectors_path.relative_to(root).as_posix()}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def semantic_rank(root: Path, task: str, include_cold: bool = False, min_score: float = 0.08) -> list[tuple[str, float, str]]:
    index_path = root / SEMANTIC_INDEX_REL
    vectors_path = root / SEMANTIC_VECTORS_REL
    if not index_path.exists() or not vectors_path.exists():
        build_semantic_index(root)
    records = {str(item.get("id")): item for item in read_jsonl(index_path)}
    query_vector = vectorize(task)
    ranked: list[tuple[str, float, str]] = []
    for item in read_jsonl(vectors_path):
        record = records.get(str(item.get("id")))
        if not record:
            continue
        rel = str(record.get("path", ""))
        tier = str(record.get("tier", "warm"))
        if not include_cold and (tier == "cold" or "/cold/" in rel):
            continue
        vector = item.get("vector")
        if not isinstance(vector, dict):
            continue
        similarity = cosine(query_vector, {str(key): float(value) for key, value in vector.items()})
        alias_boost = 0.0
        for topic, entry in load_index(root).items():
            paths = [str(path).replace("\\", "/") for path in entry.get("paths", [])]
            if rel in paths:
                alias_boost = max(alias_boost, min(0.20, score_topic(task, topic, entry.get("aliases", []), tier) / 50.0))
        tier_bonus = {"hot": 0.10, "warm": 0.03, "cold": -0.05}.get(tier, 0.0)
        score = similarity * 0.65 + alias_boost + tier_bonus
        if similarity > 0 and score >= min_score and (root / rel_path(rel)).exists():
            ranked.append((rel, score, "semantic"))
    return sorted(ranked, key=lambda row: row[1], reverse=True)


def route(root: Path, task: str, limit: int = 5, include_cold: bool = False, semantic: bool = False) -> list[str]:
    ranked = semantic_rank(root, task, include_cold=include_cold) if semantic else []
    ranked.extend(keyword_rank(root, task, include_cold=include_cold))
    matches: list[str] = []
    for rel, _score, _source in sorted(ranked, key=lambda row: row[1], reverse=True):
        if rel not in matches:
            matches.append(rel)
        if len(matches) >= limit:
            break
    return matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--task")
    parser.add_argument("--limit", "--top-k", type=int, default=5)
    parser.add_argument("--include-cold", action="store_true")
    parser.add_argument("--semantic", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.rebuild_index:
        result = build_semantic_index(root)
        if args.json:
            print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
        else:
            print(f"Semantic index rebuilt: {result['records']} records")
            print(result["index"])
            print(result["vectors"])
        return 0
    if not args.task:
        parser.error("--task is required unless --rebuild-index is used")

    paths = route(root, args.task, limit=args.limit, include_cold=args.include_cold, semantic=args.semantic)
    if args.json:
        print(json.dumps({"paths": paths, "matched": bool(paths), "semantic": args.semantic}, ensure_ascii=False, indent=2))
        return 0
    if not paths:
        print("[未命中：按新内容正常处理]")
        return 0
    for item in paths:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
