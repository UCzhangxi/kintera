"""Provenance of quoted results (N7): every provenance tag of the book names a resolvable code sha and a command.

A quoted result (a measured number, a timing, a test outcome, an error norm) is marked by the provenance tag of
STYLE section 4, in the text or in a footnote definition:

    [sha: <40-hex commit of chengcli/kintera>; deck: <input>; run: `<exact command>`, <device, precision, ranks>;
     <versions>]

N7 sharpens it. A tag fails when
  - its `sha` field holds no full 40-hex commit (as `<sha>`, `kintera@<sha>` or `chengcli/kintera@<sha>`); a phrase
    such as "the code pin" or an abbreviated sha does not count;
  - the sha does not resolve in chengcli/kintera, or is off the code pin without verified historical attribution;
  - it has no `run:` field with a backticked command;
  - it quotes a timing (a number of seconds or milliseconds, or a wall-clock time, in the tag or the rest of its
    footnote) and has no `scope:` field (what the time covers) or no `reps:` field (how many repetitions).

Historical measurements carry `historical: <full source sha>` in addition to `sha:`.
The registry tools/historical-provenance.json binds each tag to the same claim and source label in an immutable
report commit. The source must be an ancestor of the current pin. A registry is not an arbitrary SHA allowlist:
missing/wrong labels, changed claims, missing witnesses and unregistered historical labels fail. Source attribution
failures cannot be waived through the count baseline. Every check prints the verified historical count and each
current file:line/source commit as the next-repin to-do. No historical value is relabeled as a current-pin result.

The count of other failing tags per chapter may only fall. tools/provenance-baseline.json records it, and the check fails
when the file is missing, when a chapter's count differs from its baseline (a rise, or a fall not yet recorded), and,
given the target branch (`--base-ref`), when the baseline rises against the target's copy: a new chapter entry is a
rise from 0. The comparison reads the target's copy as tools/ratchet_gate.py does, and allows a rise only when the
code pin moves. `--update` writes the current counts.

Shas are resolved like tools/code_anchors.py resolves the pin: a local clone (`KINTERA_REPO`, then the repository
holding this report), else a cache under `KINTERA_REPORT_CACHE` fetched from GitHub with its history, so that historical ancestry can be decided.

usage: python3 tools/check_provenance.py [report_dir] [--update] [--list] [--base-ref REF]   (exit 0: at the baseline)
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = "chengcli/kintera"
BASELINE = "tools/provenance-baseline.json"
TARGET = "tech-report"
_TAG = re.compile(r"\[sha:\s*((?:[^\[\]]|\[[^\[\]]*\])*)\]", re.S)
_HEX = re.compile(r"(?:([\w./-]+)@)?\b([0-9a-f]{7,40})\b")
_TIMING = re.compile(r"\b\d+(?:\.\d+)?\s?(?:ms|s|min|seconds?)\b(?!\w)|\bwall[- ](?:clock|time)\b", re.I)
_CODE = re.compile(r"`[^`]+`")


# --- the book -----------------------------------------------------------------------------------------------------

def _sources(book):
    for q in sorted(Path(book).rglob("*.qmd")):
        rel = q.relative_to(book).as_posix()
        if rel.startswith(("_", ".")):
            continue
        yield rel, q.read_text(encoding="utf-8")


def _chapter(rel):
    parts = rel.split("/")
    if rel == "index.qmd":
        return "preface"
    if len(parts) < 2 or parts[0] != "chapters":
        return "book"
    m = re.match(r"(\d\d)", parts[1])
    if m:
        return f"ch{m.group(1)}"
    m = re.match(r"_?(app[a-z])", parts[-1]) or re.match(r"(app[a-z])", parts[1])
    return m.group(1) if m else parts[1]


def _fields(body):
    """The `name: value` fields of a tag body, split at top-level semicolons; the first is the sha field."""
    parts, depth, cur = [], 0, ""
    for ch in body:
        if ch == "`":
            depth ^= 1
        if ch == ";" and not depth:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    out = {"sha": parts[0].strip()}
    for p in parts[1:]:
        m = re.match(r"\s*([a-z][a-z ]*?):\s*(.*)", p, re.S)
        if m:
            out.setdefault(m.group(1).strip(), m.group(2).strip())
    return out


def _context(text, end):
    """The rest of the paragraph after a tag: for a footnote, its continuation lines, up to a blank line."""
    rest = text[end:]
    stop = re.search(r"\n\s*\n", rest)
    return rest[:stop.start()] if stop else rest


def parse_tags(rel, text):
    """Tags retain source spans and paragraph context for immutable evidence checks."""
    out = []
    for index, m in enumerate(_TAG.finditer(text)):
        prefix = re.split(r"\n\s*\n", text[:m.start()])[-1]
        suffix = _context(text, m.end())
        footnote = re.match(r"\[\^([^]]+)\]:", prefix.strip())
        out.append(dict(file=rel, line=text.count("\n", 0, m.start()) + 1,
                        chapter=_chapter(rel), index=index, identity=footnote.group(1) if footnote else f"tag:{index}",
                        start=m.start(), end=m.end(),
                        body=m.group(1), prefix=prefix, suffix=suffix,
                        fields=_fields(m.group(1)), text=m.group(1) + suffix))
    return out


def tags(book):
    return [tag for rel, text in _sources(book) for tag in parse_tags(rel, text)]


# --- shas ---------------------------------------------------------------------------------------------------------

def _git(gitdir, *args):
    return subprocess.run(["git", "-C", str(gitdir), *args], capture_output=True, text=True)


def _has(gitdir, sha):
    return _git(gitdir, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


class Resolver:
    """Resolve the current pin and verify historical source ancestry."""

    def __init__(self, report, pin, fetch=True, local=None):
        self.pin, self.fetch, self.memo = pin, fetch, {}
        cands = [Path(p) for p in ([os.environ.get("KINTERA_REPO", "")] if local is None else local) if p]
        if local is None:
            top = _git(report, "rev-parse", "--show-toplevel")
            if top.returncode == 0:
                cands.append(Path(top.stdout.strip()))
        self.local = cands
        cache = Path(os.environ.get("KINTERA_REPORT_CACHE", Path.home() / ".cache" / "kintera-report"))
        self.bare = cache / (REPO.replace("/", "__") + "-history.git")

    def _dir(self, sha):
        for d in self.local:
            if _has(d, sha) and _has(d, self.pin) and _git(d, "rev-parse", "--is-shallow-repository").stdout.strip() != "true":
                return d
        if not self.fetch:
            return None
        if not (self.bare / "HEAD").exists():
            try:
                self.bare.mkdir(parents=True, exist_ok=True)
            except OSError:
                return None
            _git(self.bare, "init", "--quiet", "--bare")
        for s in {sha, self.pin}:
            if not _has(self.bare, s):
                _git(self.bare, "fetch", "--quiet", f"https://github.com/{REPO}.git", s)
        return self.bare if _has(self.bare, sha) and _has(self.bare, self.pin) else None

    def historical(self, sha):
        """A historical source must resolve and be a strict ancestor of the current pin."""
        d = self._dir(sha)
        if d is None:
            return f"historical source {sha} does not resolve in {REPO}"
        if sha == self.pin or _git(d, "merge-base", "--is-ancestor", sha, self.pin).returncode:
            return f"historical source {sha} is not an ancestor of the code pin"
        return None

    def __call__(self, sha):
        """None for the current pin; off-pin tags need separate historical verification."""
        if sha not in self.memo:
            d = self._dir(sha)
            if d is None:
                self.memo[sha] = f"sha {sha[:12]} does not resolve in {REPO}"
            elif sha != self.pin:
                self.memo[sha] = f"sha {sha[:12]} is off the code pin {self.pin[:12]}; a verified historical label is required"
            else:
                self.memo[sha] = None
        return self.memo[sha]


# --- the check ----------------------------------------------------------------------------------------------------

def problems(tag, resolve):
    """What a tag lacks, as a list of short reasons (empty when it is complete)."""
    f, out = tag["fields"], []
    # a commit of the pinned repository: bare, or `kintera@` / `chengcli/kintera@`; another repository's sha
    # (pyharp@...) does not count
    ours = [h for repo, h in _HEX.findall(f["sha"]) if not repo or repo in (REPO.split("/")[-1], REPO)]
    full = [h for h in ours if len(h) == 40]
    if not full:
        out.append(f"short sha {ours[0]}" if ours else f"no full sha (sha field: {f['sha'][:40]!r})")
    elif len(full) != 1:
        out.append("ambiguous source sha field")
    else:
        why = resolve(full[0])
        if why:
            out.append(why)
    command = _CODE.match(f.get("run", "").lstrip())
    # A command leads the field; inline API examples embedded in prose are not invocations.
    shell_start = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*[A-Za-z0-9_./~+-]+(?:\s|$)"
    if command is None or not re.match(shell_start, command.group()[1:-1]):
        out.append("no command (no `run:` field with a backticked command)")
    if _TIMING.search(tag["text"]):
        missing = [k for k in ("scope", "reps") if not f.get(k)]
        if missing:
            out.append("timing without " + " and ".join(f"`{k}:`" for k in missing))
    return out


def read_pin(report):
    text = (Path(report) / "code_pin.yml").read_text(encoding="utf-8")
    return re.search(r"\b([0-9a-f]{40})\b", text).group(1)


HISTORICAL = "tools/historical-provenance.json"
_HISTORICAL_FIELD = re.compile(r";\s*historical:\s*[0-9a-f]{40}\s*(?=;|$|\])")


def _source(fields):
    shas = [h for repo, h in _HEX.findall(fields.get("sha", ""))
            if (not repo or repo in ("kintera", REPO)) and len(h) == 40]
    return shas[0] if len(shas) == 1 else None


def _claim(tag):
    # Preserve the complete tag and adjacent claim, allowing only whitespace reflow
    # and the added historical field. No change of numbers, commands or source labels.
    def canonical(text):
        text = _HISTORICAL_FIELD.sub("", text)
        parts, end = [], 0
        for match in re.finditer(r"(?<!`)(`+)(?!`)(.*?)(?<!`)\1(?!`)", text, re.S):
            parts.append(" ".join(text[end:match.start()].split()))
            parts.append(match.group())  # command whitespace can change shell/string semantics
            end = match.end()
        parts.append(" ".join(text[end:].split()))
        return tuple(parts)
    return tuple(canonical(tag[k]) for k in ("prefix", "body", "suffix"))


def historical_audit(report, resolve=None):
    """Verify explicit labels against immutable report witnesses, never a SHA allowlist.

    A registry row binds one tag (file + stable footnote ID) to the source recorded in the
    witness commit. Missing/changed rows, labels, claims or witnesses fail closed.
    """
    report = Path(report)
    all_tags = tags(report / "book")
    current = {(t["file"], t["identity"]): t for t in all_tags}
    valid, errors, registered, witnesses = [], [], set(), {}

    def error(key, why):
        tag = current.get(key, {})
        errors.append(dict(file=key[0], line=tag.get("line", 1),
                           chapter=tag.get("chapter", _chapter(key[0])), why=why))

    seen = set()
    for tag in all_tags:
        key = (tag["file"], tag["identity"])
        if key in seen:
            error(key, "duplicate provenance tag identity")
        seen.add(key)
    path = report / HISTORICAL
    manifest = {"version": 1, "measurements": []}
    if path.exists():
        try:
            manifest = json.loads(path.read_text())
            if manifest.get("version") != 1 or not isinstance(manifest.get("measurements"), list):
                raise ValueError("unsupported historical registry schema")
        except (ValueError, AttributeError) as exc:
            error((HISTORICAL, 0), f"invalid historical registry: {exc}")
            manifest = {"measurements": []}
    witness = manifest.get("evidence_commit", "")
    evidence_root = manifest.get("evidence_root", "")
    if (not isinstance(evidence_root, str) or Path(evidence_root).is_absolute()
            or ".." in Path(evidence_root).parts):
        error((HISTORICAL, 0), "invalid historical evidence root")
        return [], errors
    evidence_prefix = evidence_root.rstrip("/") + "/" if evidence_root else ""
    for row in manifest["measurements"]:
        if not isinstance(row, dict) or not isinstance(row.get("file"), str) or not isinstance(row.get("tag"), str):
            error((HISTORICAL, 0), "invalid historical registry row")
            continue
        key = (row["file"], row["tag"])
        if key in registered:
            error(key, "duplicate historical registry row")
            continue
        registered.add(key)
        tag, sha = current.get(key), row.get("source_sha", "")
        if tag is None:
            error(key, "registered historical measurement is missing")
            continue
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            error(key, "historical registry needs a full source commit")
            continue
        if (tag["fields"].get("historical") != sha or _source(tag["fields"]) != sha
                or len(re.findall(r"(?:^|;)\s*historical:", tag["body"])) != 1):
            error(key, "missing or wrong historical/source label; expected " + sha)
            continue
        if not isinstance(witness, str) or not re.fullmatch(r"[0-9a-f]{40}", witness):
            error(key, "historical registry needs an immutable report witness commit")
            continue
        if key[0] not in witnesses:
            old = _git(report, "show", f"{witness}:{evidence_prefix}book/{key[0]}")
            witnesses[key[0]] = {t["identity"]: t for t in parse_tags(key[0], old.stdout)} if old.returncode == 0 else {}
        old_tags = witnesses[key[0]]
        if key[1] not in old_tags:
            error(key, "historical report witness does not resolve")
            continue
        original = old_tags[key[1]]
        if _source(original["fields"]) != sha or _claim(tag) != _claim(original):
            error(key, "historical claim/source differs from its immutable report witness")
            continue
        if resolve is None:
            resolve = Resolver(report, read_pin(report))
        why = resolve.historical(sha)
        if why:
            error(key, why)
            continue
        valid.append(dict(tag, historical_sha=sha))
    for key, tag in current.items():
        if "historical" in tag["fields"] and key not in registered:
            error(key, "historical label has no verified registry witness")
    return valid, errors


def print_historical(rows):
    print(f"[historical] {len(rows)} verified measurement(s); next-repin to-do")
    for t in rows:
        print(f"  {t['file']}:{t['line']}: {t['historical_sha']}")


def violations(report, resolve=None, historical=None):
    report = Path(report)
    resolve = resolve or Resolver(report, read_pin(report))
    valid, errors = historical if historical is not None else historical_audit(report, resolve)
    accepted = {(t["file"], t["index"]) for t in valid}
    out = list(errors)
    for t in tags(report / "book"):
        resolver = (lambda sha: None) if (t["file"], t["index"]) in accepted else resolve
        for why in problems(t, resolver):
            out.append(dict(file=t["file"], line=t["line"], chapter=t["chapter"], why=why))
    return out


def counts(found):
    c = {}
    for v in found:
        c[v["chapter"]] = c.get(v["chapter"], 0) + 1
    return dict(sorted(c.items()))


def base_ref(report):
    """The target branch the baseline may not rise against, picked as the ratchet step of CI picks it.

    PROVENANCE_BASE_REF when set; in GitHub Actions, the pull request's target (GITHUB_BASE_REF) or else the previous
    tip of a push, fetched shallowly into the checkout; otherwise origin/tech-report."""
    if os.environ.get("PROVENANCE_BASE_REF"):
        return os.environ["PROVENANCE_BASE_REF"]
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return f"origin/{TARGET}"
    target = os.environ.get("GITHUB_BASE_REF", "")
    if target:
        _git(report, "fetch", "--quiet", "--depth=1", "origin", target)
        return f"origin/{target}"
    before = ""
    try:
        before = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8")).get("before") or ""
    except (KeyError, OSError, ValueError):
        pass
    if re.fullmatch(r"[0-9a-f]{40}", before) and before.strip("0"):
        _git(report, "fetch", "--quiet", "--depth=1", "origin", before)
        return before
    _git(report, "fetch", "--quiet", "--depth=1", "origin", TARGET)
    return f"origin/{TARGET}"


def raised(report, ref, baseline):
    """Chapters whose baseline rises against the baseline at `ref` (tools/ratchet_gate.py's baseline_raised, for
    this file). A `ref` that names no commit is a problem; no baseline at `ref` means this change introduces it."""
    from ratchet_gate import _git_show
    if _git(report, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode != 0:
        return [f"base ref {ref!r} names no commit here (fetch it first): the baseline cannot be compared"]
    old = _git_show(Path(report), ref, BASELINE)
    if old is None:
        return []
    old_pin = re.search(r"\b([0-9a-f]{40})\b", _git_show(Path(report), ref, "code_pin.yml") or "")
    if old_pin and old_pin.group(1) != read_pin(report):
        return []  # the pin moves in this change: which shas count moves with it
    old = json.loads(old)
    return [f"{ch}: the baseline rises {old.get(ch, 0)} -> {baseline.get(ch, 0)} against {ref}"
            for ch in sorted(set(baseline) | set(old)) if baseline.get(ch, 0) > old.get(ch, 0)]


def check(report, baseline=None, resolve=None, ref=None):
    """Return (status, messages, found): status 1 when the baseline is missing, differs from the counts, or rises
    against the baseline at `ref`."""
    report = Path(report)
    baseline = Path(baseline) if baseline else report / BASELINE
    historical = historical_audit(report, resolve)
    print_historical(historical[0])
    found = violations(report, resolve, historical)
    if not baseline.exists():
        return 1, [f"{BASELINE} is missing; write it with python3 tools/check_provenance.py --update"], found
    base = json.loads(baseline.read_text(encoding="utf-8"))
    have, msgs = counts(found), []
    for ch in sorted(set(have) | set(base)):
        n, b = have.get(ch, 0), base.get(ch, 0)
        if n > b:
            new = [v for v in found if v["chapter"] == ch]
            msgs.append(f"{ch}: {n} tag problem(s), baseline {b}; e.g. "
                        + "; ".join(f"{v['file']}:{v['line']}: {v['why']}" for v in new[:3])
                        + " (python3 tools/check_provenance.py --list lists every one)")
        elif n < b:
            msgs.append(f"{ch}: {n} tag problem(s), baseline {b}; the baseline must equal the count "
                        "(record a fall with python3 tools/check_provenance.py --update)")
    hard = historical[1] + [v for v in found if v["why"].startswith(("sha ", "short sha ", "no full sha", "ambiguous source"))]
    msgs += [f"invalid source attribution {v['file']}:{v['line']}: {v['why']}" for v in hard]
    if ref:
        msgs += raised(report, ref, base)
    return (1 if msgs else 0), msgs, found


def main(argv):
    ref = argv[argv.index("--base-ref") + 1] if "--base-ref" in argv[:-1] else None
    args = [a for a in argv if not a.startswith("--") and a != ref]
    report = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    baseline = report / BASELINE
    status, msgs, found = check(report, baseline, ref=ref)
    if "--update" in argv:
        if any(m.startswith("invalid source attribution") for m in msgs):
            print("[provenance] refusing to baseline invalid source attribution")
            for m in msgs:
                print("  " + m)
            return 1
        baseline.write_text(json.dumps(counts(found), indent=1) + "\n", encoding="utf-8")
        print(f"[provenance] baseline written: {len(found)} tag problem(s)")
        return 0
    base = json.loads(baseline.read_text(encoding="utf-8")) if baseline.exists() else {}
    print(f"[provenance] {len(tags(report / 'book'))} tags, {len(found)} problem(s); baseline {sum(base.values())}")
    if "--list" in argv:
        for v in found:
            print(f"  {v['file']}:{v['line']}: {v['why']}")
    for m in msgs:
        print(f"  ✗ {m}")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
