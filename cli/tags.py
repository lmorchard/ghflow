"""Universal Ctags indexing and query engine for ghflow.

Provides deterministic codebase symbol discovery, definition lookups,
and file outlines for interactive agents and automated burndown runners.
"""

import ast
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def find_ctags():
    """Locate a Universal Ctags or Exuberant Ctags binary on the system."""
    candidates = [
        "/opt/homebrew/bin/ctags",
        "/usr/local/bin/ctags",
        shutil.which("uctags"),
        shutil.which("ctags"),
    ]
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            try:
                proc = subprocess.run([candidate, "--version"], capture_output=True, text=True, timeout=2)
                if proc.returncode == 0 and ("Universal Ctags" in proc.stdout or "Exuberant Ctags" in proc.stdout):
                    return candidate
            except Exception:
                pass
    return None


def find_readtags():
    """Locate the readtags binary."""
    candidates = [
        "/opt/homebrew/bin/readtags",
        "/usr/local/bin/readtags",
        shutil.which("readtags"),
    ]
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            return candidate
    return None


def locate_tags_file(repo_root=None, explicit_path=None):
    """Find the tags file for a repository, checking .git/tags and root tags."""
    if explicit_path:
        p = Path(explicit_path)
        return p if p.is_file() else None
    root = Path(repo_root or os.getcwd()).resolve()

    # Check git dir first (.git/tags)
    git_path = root / ".git"
    if git_path.is_dir():
        candidate = git_path / "tags"
        if candidate.is_file():
            return candidate
    elif git_path.is_file():
        # Linked worktree: .git is a file containing "gitdir: ..."
        try:
            content = git_path.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                target = Path(content.split(":", 1)[1].strip())
                if not target.is_absolute():
                    target = (root / target).resolve()
                if (target / "tags").is_file():
                    return target / "tags"
                # Check common git dir (main repository)
                commondir_file = target / "commondir"
                if commondir_file.is_file():
                    common = Path(commondir_file.read_text(encoding="utf-8").strip())
                    if not common.is_absolute():
                        common = (target / common).resolve()
                    if (common / "tags").is_file():
                        return common / "tags"
        except Exception:
            pass

    # Check root tags files
    for name in ("tags", ".tags"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def default_tags_path(repo_root=None):
    """Return default path where tags should be generated (.git/tags if git repo)."""
    root = Path(repo_root or os.getcwd()).resolve()
    git_path = root / ".git"
    if git_path.is_dir():
        return git_path / "tags"
    elif git_path.is_file():
        try:
            content = git_path.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                target = Path(content.split(":", 1)[1].strip())
                if not target.is_absolute():
                    target = (root / target).resolve()
                # Store in main common git dir if linked worktree
                commondir_file = target / "commondir"
                if commondir_file.is_file():
                    common = Path(commondir_file.read_text(encoding="utf-8").strip())
                    if not common.is_absolute():
                        common = (target / common).resolve()
                    return common / "tags"
                return target / "tags"
        except Exception:
            pass
    return root / "tags"


def parse_tag_line(line):
    """Parse a single line from a ctags / readtags output into a dictionary."""
    line = line.strip()
    if not line or line.startswith("!_TAG_"):
        return None
    parts = line.split("\t")
    if len(parts) < 3:
        return None
    name = parts[0]
    file_path = parts[1]
    pattern_or_line = parts[2].rstrip(';"')

    fields = {}
    for f in parts[3:]:
        if ":" in f:
            k, v = f.split(":", 1)
            fields[k] = v
        elif len(f) == 1:
            fields["kind"] = f

    line_num = None
    if "line" in fields:
        try:
            line_num = int(fields["line"])
        except ValueError:
            pass
    elif pattern_or_line.isdigit():
        line_num = int(pattern_or_line)

    kind = fields.get("kind")
    # Normalize single-letter kinds if possible
    kind_map = {
        "f": "function", "c": "class", "m": "method", "v": "variable",
        "i": "interface", "e": "enum", "p": "property", "t": "typedef",
        "s": "struct", "g": "getter", "d": "macro"
    }
    if kind in kind_map:
        kind = kind_map[kind]

    return {
        "name": name,
        "path": file_path,
        "line": line_num,
        "kind": kind,
        "scope": fields.get("class") or fields.get("scope") or fields.get("struct"),
        "pattern": pattern_or_line if not pattern_or_line.isdigit() else None,
        "typeref": fields.get("typeref"),
    }


def generate_tags(repo_root=None, out_path=None, languages=None, git=None):
    """Generate or refresh tags for git-tracked source files."""
    root = Path(repo_root or os.getcwd()).resolve()
    target_out = Path(out_path).resolve() if out_path else default_tags_path(root)
    target_out.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    ctags_bin = find_ctags()

    # 1. Collect tracked source files via git ls-files
    source_patterns = [
        "*.py", "*.js", "*.mjs", "*.cjs", "*.ts", "*.tsx", "*.jsx",
        "*.go", "*.rs", "*.c", "*.cpp", "*.h", "*.hpp", "*.sh", "*.rb"
    ]
    tracked_files = []
    try:
        git_cmd = git if git else ["git"]
        proc = subprocess.run(
            [*git_cmd, "ls-files", *source_patterns],
            cwd=root, capture_output=True, text=True, timeout=15
        )
        if proc.returncode == 0:
            tracked_files = [f for f in proc.stdout.splitlines() if f.strip()]
    except Exception:
        pass

    if not tracked_files:
        # Fall back to finding files in directory if not in git
        for pat in source_patterns:
            for p in root.glob(f"**/{pat}"):
                rel = p.relative_to(root)
                parts = rel.parts
                if not any(part.startswith(".") or part in ("node_modules", "venv", ".venv") for part in parts):
                    tracked_files.append(str(rel))

    if ctags_bin:
        # Run universal-ctags with -L - (reading file list from stdin)
        cmd = [
            ctags_bin, "-L", "-", "--quiet", "-f", str(target_out),
            "--fields=+n+K+S+z", "--sort=yes"
        ]
        if languages:
            cmd.append(f"--languages={','.join(languages)}")
        proc = subprocess.run(
            cmd, cwd=root, input="\n".join(tracked_files),
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode != 0:
            return {"success": False, "error": f"ctags failed (exit {proc.returncode}): {proc.stderr.strip()}"}, 1
    else:
        # Pure Python fallback for Python files when ctags is not installed
        py_files = [f for f in tracked_files if f.endswith(".py")]
        tag_lines = []
        for pf in py_files:
            full_path = root / pf
            try:
                code = full_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(code, filename=str(pf))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    tag_lines.append(f"{node.name}\t{pf}\t{node.lineno};\"\tkind:function\tline:{node.lineno}")
                elif isinstance(node, ast.ClassDef):
                    tag_lines.append(f"{node.name}\t{pf}\t{node.lineno};\"\tkind:class\tline:{node.lineno}")
        tag_lines.sort()
        header = [
            "!_TAG_FILE_FORMAT\t2\t/extended format/",
            "!_TAG_FILE_SORTED\t1\t/sorted/",
        ]
        target_out.write_text("\n".join(header + tag_lines) + "\n", encoding="utf-8")

    duration_ms = int((time.time() - start_time) * 1000)

    # Count generated tags
    count = 0
    if target_out.is_file():
        try:
            with open(target_out, "r", encoding="utf-8", errors="ignore") as f:
                count = sum(1 for line in f if line.strip() and not line.startswith("!_TAG_"))
        except Exception:
            pass

    return {
        "success": True,
        "repo": str(root),
        "tags_file": str(target_out),
        "files_indexed": len(tracked_files),
        "symbols_indexed": count,
        "generator": ctags_bin or "python-ast-fallback",
        "duration_ms": duration_ms,
    }, 0


CODE_SUFFIXES = (
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".c", ".h", ".cpp", ".hpp", ".sh", ".rb",
)
DOC_OR_GENERATED_PREFIXES = ("docs/", ".ghflow/", "node_modules/", "tui/node_modules/")


def is_code_path(path):
    """Return whether a repository path is source code rather than docs or generated data."""
    if path.startswith(DOC_OR_GENERATED_PREFIXES) or path.endswith((".md", ".json", ".yaml", ".yml", ".lock")):
        return False
    return path.endswith(CODE_SUFFIXES)


def find_references(symbol, repo_root=None, limit=5):
    """Find up to limit code-only references to a symbol with git grep.

    Definitions come from the tags file. This companion search covers the call sites
    that a model would otherwise find with repeated grep and read calls.
    """
    root = Path(repo_root or os.getcwd()).resolve()
    clean_sym = symbol.lstrip("#")
    try:
        proc = subprocess.run(
            ["git", "grep", "-n", "-I", "-m", str(limit), "--", clean_sym],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    references = []
    for line in proc.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        path, line_no, text = parts
        if not is_code_path(path):
            continue
        references.append({
            "path": path,
            "line": int(line_no) if line_no.isdigit() else line_no,
            "text": text.strip()[:200],
        })
        if len(references) >= limit:
            break
    return references


def find_tags(symbol, repo_root=None, tags_file=None, exact=True, kind=None):
    """Find definitions matching a symbol name in the tags file."""
    root = Path(repo_root or os.getcwd()).resolve()
    tf = locate_tags_file(root, explicit_path=tags_file)
    if not tf or not tf.is_file():
        # Auto-generate if tags file does not exist
        res, code = generate_tags(repo_root=root, out_path=tags_file)
        if code != 0:
            return {"symbol": symbol, "matches": [], "error": res.get("error")}, code
        tf = Path(res["tags_file"])

    matches = []
    readtags_bin = find_readtags()

    clean_sym = symbol.lstrip("#")
    if readtags_bin and tf.is_file():
        cmd = [readtags_bin, "-t", str(tf), "-e", "-n"]
        if not exact:
            cmd.append("-p")
        cmd.append(clean_sym)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if proc.returncode == 0 and proc.stdout.strip():
                for line in proc.stdout.splitlines():
                    entry = parse_tag_line(line)
                    if entry:
                        if kind and entry.get("kind") != kind:
                            continue
                        matches.append(entry)
        except Exception:
            pass

    if not matches and tf.is_file():
        # Pure-Python fallback search through sorted tags file
        clean_lower = clean_sym.lower()
        try:
            with open(tf, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("!_TAG_"):
                        continue
                    parts = line.split("\t", 2)
                    if not parts:
                        continue
                    tag_name = parts[0]
                    if exact:
                        if tag_name == clean_sym:
                            entry = parse_tag_line(line)
                            if entry and (not kind or entry.get("kind") == kind):
                                matches.append(entry)
                        elif tag_name > clean_sym:
                            # Because file is sorted, if tag_name is past symbol in ASCII, we can stop
                            # only if case matches
                            if not tag_name.lower().startswith(clean_lower):
                                pass
                    else:
                        if clean_lower in tag_name.lower():
                            entry = parse_tag_line(line)
                            if entry and (not kind or entry.get("kind") == kind):
                                matches.append(entry)
        except Exception:
            pass

    return {
        "symbol": symbol,
        "count": len(matches),
        "tags_file": str(tf),
        "matches": matches,
    }, 0


def outline_file(file_path, repo_root=None, tags_file=None):
    """List all symbols defined in a given source file, ordered by line number."""
    root = Path(repo_root or os.getcwd()).resolve()
    target_file = Path(file_path).resolve()
    try:
        rel_path = str(target_file.relative_to(root))
    except ValueError:
        rel_path = str(target_file)

    tf = locate_tags_file(root, explicit_path=tags_file)
    if not tf or not tf.is_file():
        res, code = generate_tags(repo_root=root, out_path=tags_file)
        if code != 0:
            return {"file": rel_path, "symbols": [], "error": res.get("error")}, code
        tf = Path(res["tags_file"])

    symbols = []
    try:
        with open(tf, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("!_TAG_"):
                    continue
                parts = line.split("\t", 3)
                if len(parts) >= 2 and (parts[1] == rel_path or rel_path.endswith(parts[1]) or parts[1].endswith(rel_path)):
                    entry = parse_tag_line(line)
                    if entry:
                        symbols.append(entry)
    except Exception as e:
        return {"file": rel_path, "symbols": [], "error": str(e)}, 1

    # Sort symbols by line number
    symbols.sort(key=lambda s: (s.get("line") or 0, s.get("name") or ""))

    return {
        "file": rel_path,
        "count": len(symbols),
        "tags_file": str(tf),
        "symbols": symbols,
    }, 0
