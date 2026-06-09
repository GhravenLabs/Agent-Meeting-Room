import os
from pathlib import Path


MAX_FILES = 80
MAX_TOTAL_BYTES = 900_000
MAX_SNIPPET_CHARS = 1_200

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "target",
    ".next",
    ".turbo",
    ".cache",
}

IGNORE_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "uv.lock",
}

TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

IMPORTANT_NAMES = {
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
}


def _is_hidden_or_ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def _is_text_candidate(path: Path) -> bool:
    if path.name in IGNORE_FILES:
        return False
    if path.name in IMPORTANT_NAMES:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def _score_file(root: Path, path: Path) -> tuple:
    rel = path.relative_to(root).as_posix()
    depth = rel.count("/")
    important = 0 if path.name in IMPORTANT_NAMES else 1
    source = 0 if path.suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx", ".rs"} else 1
    return important, source, depth, len(rel), rel.lower()


def _read_preview(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text[:MAX_SNIPPET_CHARS].strip()


def summarize_project(project_path: str) -> dict:
    root = Path(project_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("Project path must be an existing folder")

    candidates = []
    skipped = 0
    total_bytes = 0

    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [
            item for item in dirs
            if item not in IGNORE_DIRS and not item.startswith(".")
        ]
        if _is_hidden_or_ignored(current_path.relative_to(root) if current_path != root else Path("")):
            continue

        for name in files:
            path = current_path / name
            if name.startswith(".") or not _is_text_candidate(path):
                skipped += 1
                continue
            try:
                size = path.stat().st_size
            except OSError:
                skipped += 1
                continue
            if size > 180_000:
                skipped += 1
                continue
            candidates.append(path)

    selected = []
    for path in sorted(candidates, key=lambda item: _score_file(root, item)):
        try:
            size = path.stat().st_size
        except OSError:
            skipped += 1
            continue
        if len(selected) >= MAX_FILES or total_bytes + size > MAX_TOTAL_BYTES:
            skipped += 1
            continue
        preview = _read_preview(path)
        if not preview:
            skipped += 1
            continue
        total_bytes += size
        selected.append({
            "path": path.relative_to(root).as_posix(),
            "size": size,
            "preview": preview,
        })

    extensions = {}
    for path in selected:
        suffix = Path(path["path"]).suffix.lower() or "[no extension]"
        extensions[suffix] = extensions.get(suffix, 0) + 1

    summary = {
        "root": str(root),
        "name": root.name,
        "file_count": len(selected),
        "skipped_count": skipped,
        "total_bytes": total_bytes,
        "extensions": dict(sorted(extensions.items(), key=lambda item: (-item[1], item[0]))),
        "files": selected,
    }
    summary["context"] = render_project_context(summary)
    return summary


def render_project_context(summary: dict) -> str:
    lines = [
        "PROJECT CONTEXT LOADED:",
        f"- Name: {summary.get('name', 'Project')}",
        f"- Root: {summary.get('root', '')}",
        f"- Indexed files: {summary.get('file_count', 0)}",
    ]
    extensions = summary.get("extensions") or {}
    if extensions:
        lines.append(
            "- File types: "
            + ", ".join(f"{ext} ({count})" for ext, count in list(extensions.items())[:8])
        )
    lines.extend(["", "Important file previews:"])
    for item in (summary.get("files") or [])[:18]:
        lines.extend([
            "",
            f"--- {item.get('path')} ---",
            item.get("preview", ""),
        ])
    return "\n".join(lines).strip()
