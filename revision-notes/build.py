"""
build.py — generate a static HTML revision-notes site from the note files
under every topic folder next to this script (Month1, Month2,
PluginArchitecture, Solid7DesignPatterns, SystemDesign, and any folder you
add later).

Run from this folder:
    python build.py

It reads .txt and .md notes and never modifies them. The output is
deterministic, so re-run any time you add or edit a note. GitHub Actions also
runs this on every push (see ../.github/workflows/deploy.yml), so once it is
set up you usually don't need to run it by hand at all.

Two folder shapes are supported automatically:
    Month1/week1/spring1.txt        (topic -> week -> notes   : "nested")
    SystemDesign/Day1.txt           (topic -> notes           : "flat")
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

# ---------- paths --------------------------------------------------------

HERE = Path(__file__).resolve().parent
SOURCE_ROOT = HERE.parent          # the Spring/ folder (holds the topic dirs)
OUTPUT_ROOT = HERE                  # revision-notes/  (the published site root)

SITE_TITLE = "Tech Revision Notes"

NOTE_SUFFIXES = {".txt", ".md"}

# Folders that are never treated as topics (this generator's own home, VCS,
# tooling, caches). Everything else at the top level that contains notes is a
# topic and shows up on the site automatically.
SKIP_DIRS = {
    "revision-notes", ".git", ".github", "__pycache__",
    ".idea", ".vscode", "node_modules", "assets",
}

# ---------- block classification ----------------------------------------

DIAGRAM_CHARS = set("→↓↑←─│┌┐└┘├┤┬┴┼╔╗╚╝═║╠╣╦╩╬▼▲►◄")
ARROW_TOKENS = ("-->", "==>", "<--")

# A line is "code-like" if it has structural Java/SQL/config markers that
# never appear in English prose written by a human.
STRONG_CODE_LINE_RE = re.compile(
    r"^\s*@[A-Z]\w*\s*(\(.*\))?\s*$"                         # standalone @Annotation
    r"|^\s*@[A-Z]\w*\s*(\(.*\))?\s+[\w<>\[\]]+\s+\w+\s*[(;=]"  # @Anno Type name(... or =
    r"|^\s*(public|private|protected|static|final|abstract|synchronized)\s+[\w<>\[\],\s]"
    r"|^\s*(import|package)\s+[\w.*]+;"
    r"|^\s*(class|interface|enum)\s+[A-Z]\w*"
    r"|^\s*(if|else if|for|while|do|switch|return|throw|try|catch|finally)\s*[({]"
    r"|^\s*}\s*(else|catch|finally|while)?\s*[({]?\s*;?$"
    r"|^\s*\{\s*$"
    r"|^\s*\}\s*[;)]?$"
    r"|\);\s*$"                                              # method call;
    r"|^\s*//"                                               # // comment
    r"|^\s*/\*"                                              # /* comment
    r"|^\s*\*\s"                                             # javadoc body
    r"|^\s*[A-Z]\w*(<[^>]*>)?\s+\w+\s*=\s*new\s+"            # Type x = new ...
    r"|^\s*[a-zA-Z_]\w*\.\w+\([^)]*\)\s*[.;]"                # obj.method(...) chain
)

# Words common in English prose. If a line has several of these AND multiple
# real words, it's overwhelmingly prose even if it mentions "class" or "new".
PROSE_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "this", "that",
    "these", "those", "with", "when", "then", "but", "because", "so",
    "of", "to", "in", "on", "at", "by", "for", "from", "we", "you",
    "i", "it", "as", "if", "and", "or", "not", "have", "has", "had",
    "be", "been", "being", "do", "does", "did", "will", "would", "can",
    "could", "should", "may", "might", "must", "into", "out", "over",
    "which", "what", "where", "how", "why", "your", "their", "our",
    "they", "them", "he", "she", "him", "her", "us", "all", "any",
    "some", "every", "each", "no", "only", "just", "now", "also",
}

# ---------- data model ---------------------------------------------------

@dataclass
class Page:
    """One generated page (one .txt or .md file)."""
    title: str           # full page title, e.g. "Spring 15 — JPA + Hibernate Config"
    short_title: str     # compact label for the index list
    number: str          # extracted number prefix (for the index badge) or ""
    section: str         # top-level topic folder, e.g. "Month1" / "SystemDesign"
    group: str | None    # sub-folder (e.g. "week1") or None for flat topics
    src_path: Path       # absolute source path (.txt/.md) — read only
    out_path: Path       # absolute output .html path
    rel_href: str        # path from index.html to this page

    @property
    def is_markdown(self) -> bool:
        return self.src_path.suffix.lower() == ".md"


# ---------- naming helpers ----------------------------------------------

def slugify(name: str) -> str:
    """Convert a filename stem into a URL-friendly slug."""
    s = name.strip()
    s = s.replace("+", "-plus-").replace("&", "-and-")
    s = re.sub(r"[^\w\-. ]+", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-").lower()


def _space_out(name: str) -> str:
    """Insert spaces at camelCase and letter/number boundaries."""
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    s = re.sub(r"(\d)([A-Za-z])", r"\1 \2", s)
    s = s.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()


def humanize_section(name: str) -> str:
    """'Solid7DesignPatterns' -> 'Solid 7 Design Patterns', 'Month1' -> 'Month 1'."""
    return _space_out(name)


def humanize_group(name: str) -> str:
    """'week1' -> 'Week 1', 'Week2' -> 'Week 2'."""
    out = _space_out(name)
    return out[:1].upper() + out[1:] if out else out


def _clean_topic(topic: str) -> str:
    topic = topic.strip(" -_")
    topic = re.sub(r"([a-z])([A-Z])", r"\1 \2", topic)
    topic = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", topic)
    topic = topic.replace("_", " ")
    return re.sub(r"\s+", " ", topic).strip()


def humanize_title(stem: str) -> tuple[str, str]:
    """
    From a filename stem like 'Spring29MicroServices', 'Day2Singleton', or
    'Day1-ClassLoader Fundamentals' produce (full_title, short_title).
    """
    raw = stem.strip()
    # Leading "Word + number" (Spring15, Day2, Spring 29, Day1-...)
    m = re.match(r"^([A-Za-z]+)\s*(\d+)\b\s*[-_ ]*(.*)$", raw)
    if m:
        prefix, num, topic = m.groups()
        # Keep known labels title-cased; leave other prefixes as authored.
        if prefix.lower() in ("spring", "day"):
            prefix = prefix.capitalize()
        topic = _clean_topic(topic)
        if topic:
            return f"{prefix} {num} — {topic}", f"{prefix} {num}: {topic}"
        return f"{prefix} {num}", f"{prefix} {num}"
    # No leading number: just prettify the whole stem.
    pretty = _clean_topic(raw)
    return pretty, pretty


def natural_key(s: str) -> list:
    """Sort 'Spring2' before 'Spring10' and 'week2' before 'week10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def day_sort_key(stem: str) -> tuple:
    """Order notes by embedded day number when present, else alphabetically."""
    m = re.search(r"[Dd]ay\s*(\d+)", stem)
    if not m:
        m = re.search(r"(\d+)", stem)
    if m:
        return (0, int(m.group(1)), stem.lower())
    return (1, 0, stem.lower())


# ---------- plain-text (.txt) rendering ---------------------------------

def split_blocks(text: str) -> list[list[str]]:
    """Split into blocks separated by blank lines."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line.rstrip())
    if current:
        blocks.append(current)
    return blocks


def _strip_line_comment(line: str) -> str:
    """Drop a trailing ``// comment`` so the prose that lives in code comments
    doesn't make a real code line look like an English sentence. Leaves
    ``https://`` URLs intact."""
    idx = line.find("//")
    if idx > 0 and not line[:idx].rstrip().endswith(":"):
        return line[:idx]
    return line


def looks_prosey(line: str) -> bool:
    """Line reads like an English sentence — many short common words."""
    words = [w.lower().strip(".,;:!?\"'()[]") for w in line.split()]
    if len(words) < 5:
        return False
    connectors = sum(1 for w in words if w in PROSE_WORDS)
    return connectors >= 2


def is_diagram_block(block: list[str]) -> bool:
    """True only for real ASCII diagrams / arrow flows — never for prose that
    merely contains a '→' used as "leads to". A line counts toward the diagram
    only if it carries diagram glyphs AND does not read like a sentence; a
    single prosey line vetoes the whole block."""
    non_blank = [l for l in block if l.strip()]
    if len(non_blank) < 2:
        return False
    diagram_lines = 0
    prose_lines = 0
    for line in non_blank:
        prosey = looks_prosey(line)
        has_glyph = (any(ch in line for ch in DIAGRAM_CHARS)
                     or any(tok in line for tok in ARROW_TOKENS))
        if has_glyph and not prosey:
            diagram_lines += 1
        elif prosey:
            prose_lines += 1
    if prose_lines:
        return False
    return diagram_lines >= 2 and diagram_lines >= (len(non_blank) + 1) // 2


# SQL statements and key=value config lines that the Java-oriented code detector
# misses. Kept conservative: a block only counts as SQL/config when several
# lines match AND no line reads like English prose.
_SQL_LINE_RE = re.compile(
    r"^\s*(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|CREATE\s+(TABLE|INDEX|DATABASE)"
    r"|ALTER\s+TABLE|DROP\s+(TABLE|INDEX)|FROM|WHERE|(LEFT|RIGHT|INNER|OUTER)\s+JOIN"
    r"|JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|VALUES|FOREIGN\s+KEY|PRIMARY\s+KEY"
    r"|ON\s+DELETE|ON\s+UPDATE|REFERENCES)\b",
    re.IGNORECASE,
)
_CONFIG_LINE_RE = re.compile(r"^\s*[\w.][\w.\-]*\s*=\s*\S")


def is_sqlish_block(block: list[str]) -> bool:
    non_blank = [l for l in block if l.strip()]
    if len(non_blank) < 2:
        return False
    sql = sum(1 for l in non_blank if _SQL_LINE_RE.match(l))
    cfg = sum(1 for l in non_blank if _CONFIG_LINE_RE.match(l))
    prose = sum(1 for l in non_blank if looks_prosey(l))
    if prose:
        return False
    if sql >= 2 and sql >= len(non_blank) // 2:
        return True
    if cfg >= 2 and cfg >= (len(non_blank) + 1) // 2:
        return True
    return False


def is_code_block(block: list[str]) -> bool:
    """Tightened code detector — requires structural markers, not just keywords."""
    if not block:
        return False
    code_score = 0
    prose_score = 0
    has_brace = False
    for line in block:
        stripped = line.strip()
        if not stripped:
            continue
        if STRONG_CODE_LINE_RE.search(line):
            code_score += 2
        elif stripped.endswith(";"):
            code_score += 1
        elif stripped in ("{", "}", "};", "});", "})"):
            code_score += 2
            has_brace = True
        if "{" in stripped or "}" in stripped:
            has_brace = True
        if looks_prosey(_strip_line_comment(line)):
            prose_score += 2
    if has_brace and code_score >= 2 and code_score >= prose_score:
        return True
    return code_score >= 4 and code_score > prose_score * 2


HEADER_PATTERNS = [
    re.compile(r"^\s*TOPIC\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*PART\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*STEP\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*Problem\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*Solution\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*Chapter\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*Day\s+\d+", re.IGNORECASE),
]

EMOJI_HEADER_RE = re.compile(r"^[\U0001F300-\U0001FAFF☀-➿]")


# Lowercase words that betray a mid-sentence prose line masquerading as a
# short Title-Case heading (e.g. "High Level Module depends on EmailSender").
_HEADER_STOPWORDS = {
    "is", "are", "was", "were", "the", "a", "an", "of", "to", "in", "on",
    "depends", "uses", "use", "has", "have", "needs", "means", "returns",
    "extends", "implements", "contains", "between", "with", "for", "and",
}


def header_level(block: list[str]) -> int | None:
    """Return 2 or 3 if the block is a single-line header, else None."""
    if len(block) != 1:
        return None
    line = block[0].strip()
    if not line or len(line) > 90:
        return None
    # Explicit section markers (TOPIC/PART/STEP/Problem/Solution/Chapter/Day + N)
    # are unambiguous headers — accept them before the punctuation guards, so a
    # trailing ":" / an "(aside)" / an "— subtitle" doesn't demote them.
    for pat in HEADER_PATTERNS:
        if pat.match(line):
            return 2
    if line.endswith((".", "?", ",", ";", ":", "!")):
        return None
    if "{" in line or "}" in line or "(" in line or ")" in line or ";" in line:
        return None
    if " " in line and ":" in line:
        return None
    if EMOJI_HEADER_RE.match(line):
        return 2
    words = line.split()
    if 1 <= len(words) <= 8 and len(line) <= 60:
        cap_words = sum(1 for w in words if w[:1].isupper())
        prosey = any(w.lower() in _HEADER_STOPWORDS for w in words)
        enough_caps = cap_words >= 2 if len(words) >= 2 else cap_words >= 1
        if enough_caps and not prosey:
            return 3
    return None


def classify(block: list[str]) -> str:
    if header_level(block) is not None:
        return "header"
    if is_code_block(block):
        return "code"
    if is_sqlish_block(block):
        return "code"
    if is_diagram_block(block):
        return "diagram"
    return "prose"


# Bare language-fence labels that sometimes lead a code block in the source
# (a leftover ```java / ```bash marker on its own line).
_FENCE_LABELS = {
    "java", "bash", "sh", "shell", "console", "sql", "json", "xml", "yaml",
    "yml", "groovy", "properties", "kotlin", "text", "plaintext", "http",
}


def render_block(block: list[str], kind: str) -> str:
    if kind == "diagram":
        body = "\n".join(html.escape(l) for l in block)
        return f'<pre class="diagram">{body}</pre>'
    if kind == "code":
        lines = list(block)
        while lines and not lines[0].strip():
            lines.pop(0)
        # A lone language label on the first line becomes the highlight hint;
        # otherwise emit no class and let highlight.js auto-detect (so SQL/JSON
        # notes aren't force-coloured as Java).
        lang = ""
        if lines and lines[0].strip().lower() in _FENCE_LABELS:
            lang = lines[0].strip().lower()
            lines = lines[1:]
        body = "\n".join(html.escape(l) for l in lines)
        cls = f' class="language-{lang}"' if lang else ""
        return f'<pre class="code-block"><code{cls}>{body}</code></pre>'
    if kind == "header":
        lvl = header_level(block)
        return f'<h{lvl} class="section">{html.escape(block[0].strip())}</h{lvl}>'
    paragraphs = "\n".join(
        f"<p>{html.escape(l.strip())}</p>" for l in block if l.strip()
    )
    return f'<div class="prose">{paragraphs}</div>'


def merge_code_runs(blocks: list[list[str]], kinds: list[str]) -> tuple[list[list[str]], list[str]]:
    """A short prose block sandwiched between two code blocks is almost always
    a stray code line; reclassify and merge the three into one code block."""
    out_blocks: list[list[str]] = []
    out_kinds: list[str] = []
    i = 0
    while i < len(blocks):
        if (
            kinds[i] == "code"
            and i + 2 < len(blocks)
            and kinds[i + 1] == "prose"
            and kinds[i + 2] == "code"
            and len(blocks[i + 1]) <= 2
            and not any(looks_prosey(l) for l in blocks[i + 1])
        ):
            merged = blocks[i] + [""] + blocks[i + 1] + [""] + blocks[i + 2]
            out_blocks.append(merged)
            out_kinds.append("code")
            i += 3
            continue
        if (
            kinds[i] == "code"
            and out_kinds
            and out_kinds[-1] == "code"
            and len(out_blocks[-1]) + len(blocks[i]) < 200
        ):
            out_blocks[-1] = out_blocks[-1] + [""] + blocks[i]
            i += 1
            continue
        out_blocks.append(blocks[i])
        out_kinds.append(kinds[i])
        i += 1
    return out_blocks, out_kinds


def _is_explicit_header_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 90:
        return False
    return any(pat.match(s) for pat in HEADER_PATTERNS)


def peel_headers(blocks: list[list[str]]) -> list[list[str]]:
    """Split leading explicit-header lines (Part/Step/TOPIC/Day N …) off the
    front of a block. Notes often run a section header straight into the code
    or prose that follows with no blank line between them."""
    out: list[list[str]] = []
    for b in blocks:
        i = 0
        while i < len(b) and _is_explicit_header_line(b[i]):
            out.append([b[i]])
            i += 1
        if i < len(b):
            out.append(b[i:])
    return out


def _is_lead_prose_line(line: str) -> bool:
    """A line that clearly reads as an English sentence, not code."""
    s = line.strip()
    if not s or not looks_prosey(_strip_line_comment(line)):
        return False
    if STRONG_CODE_LINE_RE.search(line):
        return False
    if s[0] in "{}/@*":            # brace, comment, annotation, javadoc
        return False
    if s[-1] in ";{}),":          # ends like a statement
        return False
    return True


def peel_prose_from_code(blocks: list[list[str]], kinds: list[str]
                         ) -> tuple[list[list[str]], list[str]]:
    """Peel plain-prose lead-in / trailing lines out of a code block into their
    own prose blocks (looks_prosey is a strong discriminator, so real Java is
    left intact)."""
    out_b: list[list[str]] = []
    out_k: list[str] = []
    for b, k in zip(blocks, kinds):
        if k != "code":
            out_b.append(b)
            out_k.append(k)
            continue
        lead = 0
        while lead < len(b) and b[lead].strip() and _is_lead_prose_line(b[lead]):
            lead += 1
        trail = len(b)
        while trail > lead and b[trail - 1].strip() and _is_lead_prose_line(b[trail - 1]):
            trail -= 1
        if lead == 0 and trail == len(b):
            out_b.append(b)
            out_k.append("code")
            continue
        if lead > 0:
            out_b.append(b[:lead])
            out_k.append("prose")
        core = b[lead:trail]
        if any(l.strip() for l in core):
            out_b.append(core)
            out_k.append("code")
        if trail < len(b):
            out_b.append(b[trail:])
            out_k.append("prose")
    return out_b, out_k


def render_txt(text: str) -> str:
    blocks = peel_headers(split_blocks(text))
    kinds = [classify(b) for b in blocks]
    blocks, kinds = merge_code_runs(blocks, kinds)
    blocks, kinds = peel_prose_from_code(blocks, kinds)
    return "\n".join(render_block(b, k) for b, k in zip(blocks, kinds))


# ---------- markdown (.md) rendering ------------------------------------
# A small, dependency-free renderer covering the constructs used in the notes:
# ATX headings, fenced code, tables, bullet/numbered lists, blockquotes,
# horizontal rules, and inline bold / italic / code / links.

_FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([\w+#.-]*)\s*$")
_ATX_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_HR_RE = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
_UL_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_BQ_RE = re.compile(r"^\s*>\s?(.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)+\|?\s*$")

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_BOLD_US_RE = re.compile(r"__(.+?)__")
_ITALIC_RE = re.compile(r"(?<![\*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![\*\w])")
_ITALIC_US_RE = re.compile(r"(?<![_\w])_(?!\s)([^_]+?)(?<!\s)_(?![_\w])")


_CODE_PLACEHOLDER_RE = re.compile("\x00(\\d+)\x00")


def render_inline(text: str) -> str:
    """Render inline markdown to HTML.

    Code spans are stashed as placeholders *before* emphasis is applied, so
    their contents are never treated as markup — yet bold/italic that spans a
    code span (e.g. ``**`@Mock` vs `@InjectMocks`?**``) still pairs correctly,
    because on the emphasis pass the code span is just an opaque token.
    """
    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    esc = html.escape(_INLINE_CODE_RE.sub(stash, text))
    esc = _LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', esc)
    esc = _BOLD_RE.sub(r"<strong>\1</strong>", esc)
    esc = _BOLD_US_RE.sub(r"<strong>\1</strong>", esc)
    esc = _ITALIC_RE.sub(r"<em>\1</em>", esc)
    esc = _ITALIC_US_RE.sub(r"<em>\1</em>", esc)
    return _CODE_PLACEHOLDER_RE.sub(
        lambda m: f"<code>{html.escape(codes[int(m.group(1))])}</code>", esc
    )


def _split_table_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


_TASK_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")


def _render_li(item: str) -> str:
    """Render a list item, turning GitHub '[ ]' / '[x]' task syntax into a real
    (disabled) checkbox instead of leaving the brackets in the text."""
    m = _TASK_RE.match(item)
    if m:
        checked = " checked" if m.group(1).lower() == "x" else ""
        return (f'<li class="task"><input type="checkbox" disabled{checked}> '
                f'{render_inline(m.group(2))}</li>')
    return f"<li>{render_inline(item)}</li>"


def extract_leading_h1(text: str) -> tuple[str | None, str]:
    """If the doc starts with a level-1 ATX heading, return (title, rest) with
    that heading removed so it isn't repeated below the page title."""
    lines = text.split("\n")
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx < len(lines):
        m = re.match(r"^\s{0,3}#\s+(.*?)\s*#*\s*$", lines[idx])
        if m:
            title = re.sub(r"[*`]", "", m.group(1)).strip()
            rest = "\n".join(lines[:idx] + lines[idx + 1:])
            return title, rest
    return None, text


def render_markdown(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    para: list[str] = []
    i, n = 0, len(lines)

    def flush_para() -> None:
        if para:
            joined = " ".join(l.strip() for l in para).strip()
            if joined:
                out.append(f"<p>{render_inline(joined)}</p>")
            para.clear()

    while i < n:
        line = lines[i]

        mfence = _FENCE_RE.match(line)
        if mfence:
            flush_para()
            fence, lang = mfence.group(1), mfence.group(2)
            i += 1
            code_lines: list[str] = []
            while i < n and not lines[i].strip().startswith(fence):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            body = "\n".join(html.escape(cl) for cl in code_lines)
            cls = f' class="language-{lang}"' if lang else ' class="language-plaintext"'
            out.append(f'<pre class="code-block"><code{cls}>{body}</code></pre>')
            continue

        if line.strip() == "":
            flush_para()
            i += 1
            continue

        if _HR_RE.match(line):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        matx = _ATX_RE.match(line)
        if matx:
            flush_para()
            level = len(matx.group(1))
            tag = "h2" if level <= 2 else ("h3" if level == 3 else "h4")
            out.append(f'<{tag} class="section">{render_inline(matx.group(2).strip())}</{tag}>')
            i += 1
            continue

        if line.lstrip().startswith("|") and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]):
            flush_para()
            header = _split_table_row(line)
            i += 2
            body_rows: list[str] = []
            while i < n and lines[i].lstrip().startswith("|") and lines[i].strip():
                cells = _split_table_row(lines[i])
                tds = "".join(f"<td>{render_inline(c)}</td>" for c in cells)
                body_rows.append(f"<tr>{tds}</tr>")
                i += 1
            ths = "".join(f"<th>{render_inline(c)}</th>" for c in header)
            out.append(
                '<div class="table-wrap"><table><thead><tr>'
                + ths + "</tr></thead><tbody>" + "".join(body_rows) + "</tbody></table></div>"
            )
            continue

        if _BQ_RE.match(line):
            flush_para()
            quoted: list[str] = []
            while i < n and _BQ_RE.match(lines[i]):
                quoted.append(_BQ_RE.match(lines[i]).group(1))
                i += 1
            out.append(f"<blockquote>{render_inline(' '.join(q.strip() for q in quoted))}</blockquote>")
            continue

        if _UL_RE.match(line):
            flush_para()
            items: list[str] = []
            while i < n and _UL_RE.match(lines[i]):
                items.append(_UL_RE.match(lines[i]).group(1))
                i += 1
            out.append("<ul>" + "".join(_render_li(it) for it in items) + "</ul>")
            continue

        if _OL_RE.match(line):
            flush_para()
            items = []
            while i < n and _OL_RE.match(lines[i]):
                items.append(_OL_RE.match(lines[i]).group(1))
                i += 1
            out.append("<ol>" + "".join(_render_li(it) for it in items) + "</ol>")
            continue

        para.append(line)
        i += 1

    flush_para()
    return '<div class="md-content">\n' + "\n".join(out) + "\n</div>"


# ---------- page + index templates --------------------------------------

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · {site_title}</title>
<link rel="stylesheet" href="{css_href}">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css" media="(prefers-color-scheme: dark)">
</head>
<body>
<header class="site-header">
  <div class="nav-row">
    <a href="{index_href}">← All Notes</a>
    <span class="crumb-sep">/</span>
    <span class="crumb">{section}</span>
    {group_crumb}
  </div>
</header>
<main>
  <h1 class="page-title">{title}</h1>
  <p class="page-subtitle">{subtitle}</p>
  {content}
  <nav class="pager">
    {prev_link}
    {next_link}
  </nav>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/sql.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/xml.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/json.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/properties.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/groovy.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/yaml.min.js"></script>
<script>hljs.highlightAll();</script>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{site_title}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
  <div class="nav-row">
    <strong>{site_title}</strong>
  </div>
</header>
<main>
  <h1 class="page-title">{site_title}</h1>
  <p class="page-subtitle">Interview-prep notes — tap any day to read.</p>
  <div class="intro">
    A revision-friendly view of every note in this repo. The source
    <code>.txt</code> and <code>.md</code> files are never modified; this page
    and everything it links to is generated by <code>build.py</code>.
  </div>
  {body}
</main>
</body>
</html>
"""


def build_index(pages: list[Page]) -> str:
    # section -> group(str|None) -> [pages], preserving discovery order.
    by_section: dict[str, dict[str | None, list[Page]]] = {}
    for p in pages:
        by_section.setdefault(p.section, {}).setdefault(p.group, []).append(p)

    parts: list[str] = [f'<p class="note-count">{len(pages)} notes total</p>']
    for section, groups in by_section.items():
        section_total = sum(len(v) for v in groups.values())
        parts.append('<section class="month-section">')
        parts.append(
            f'<h2>{html.escape(humanize_section(section))}'
            f'<span class="count">{section_total} note{"s" if section_total != 1 else ""}</span></h2>'
        )
        is_flat = list(groups.keys()) == [None]
        for group, group_pages in groups.items():
            if is_flat:
                parts.append(_day_list(group_pages))
            else:
                label = humanize_group(group) if group is not None else "Notes"
                parts.append(
                    f'<details class="week" open><summary>{html.escape(label)}'
                    f'<span class="count">{len(group_pages)} note'
                    f'{"s" if len(group_pages) != 1 else ""}</span></summary>'
                    + _day_list(group_pages) + "</details>"
                )
        parts.append("</section>")
    return "\n".join(parts)


def _day_list(pages: list[Page]) -> str:
    items = ['<ul class="day-list">']
    for page in pages:
        num = html.escape(page.number) if page.number else "•"
        items.append(
            f'<li><a href="{html.escape(page.rel_href)}">'
            f'<span class="num">{num}</span> {html.escape(page.short_title)}</a></li>'
        )
    items.append("</ul>")
    return "\n".join(items)


# ---------- discovery ----------------------------------------------------

def _is_blank_note(path: Path) -> bool:
    try:
        return not path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return True


def _note_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(directory.iterdir(), key=lambda p: day_sort_key(p.stem)):
        if not (p.is_file() and p.suffix.lower() in NOTE_SUFFIXES):
            continue
        if _is_blank_note(p):
            print(f"  skipped (empty note): {p.relative_to(SOURCE_ROOT)}")
            continue
        files.append(p)
    return files


def _make_page(src: Path, section: str, group: str | None) -> Page:
    full_title, short_title = humanize_title(src.stem)
    num_match = re.search(r"\d+", src.stem)
    number = num_match.group(0) if num_match else ""
    rel_parts = [section] + ([group] if group else []) + [slugify(src.stem) + ".html"]
    out_path = OUTPUT_ROOT.joinpath(*rel_parts)
    return Page(
        title=full_title,
        short_title=short_title,
        number=number,
        section=section,
        group=group,
        src_path=src,
        out_path=out_path,
        rel_href=out_path.relative_to(OUTPUT_ROOT).as_posix(),
    )


def discover_pages() -> list[Page]:
    """Find every topic folder next to this script and collect its notes.
    Supports flat topics (notes directly inside) and nested topics (notes in
    one level of sub-folders such as weeks)."""
    pages: list[Page] = []
    topic_dirs = sorted(
        (d for d in SOURCE_ROOT.iterdir()
         if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith(".")),
        key=lambda d: natural_key(d.name),
    )
    for topic in topic_dirs:
        section_pages: list[Page] = []
        # notes sitting directly in the topic folder (flat shape)
        for src in _note_files(topic):
            section_pages.append(_make_page(src, topic.name, None))
        # notes inside one level of sub-folders (nested shape)
        subdirs = sorted(
            (d for d in topic.iterdir() if d.is_dir() and not d.name.startswith(".")),
            key=lambda d: natural_key(d.name),
        )
        for sub in subdirs:
            for src in _note_files(sub):
                section_pages.append(_make_page(src, topic.name, sub.name))
        if section_pages:
            pages.extend(section_pages)
    return pages


# ---------- writing ------------------------------------------------------

def _rel_link(from_page: Page, to_page: Page) -> str:
    """Forward-slash relative path from one page's folder to another page's file."""
    from_parts = from_page.out_path.relative_to(OUTPUT_ROOT).parts[:-1]
    to_parts = to_page.out_path.relative_to(OUTPUT_ROOT).parts
    i = 0
    while i < len(from_parts) and i < len(to_parts) - 1 and from_parts[i] == to_parts[i]:
        i += 1
    ups = "../" * (len(from_parts) - i)
    return ups + "/".join(to_parts[i:])


def write_page(page: Page, prev: Page | None, nxt: Page | None) -> None:
    page.out_path.parent.mkdir(parents=True, exist_ok=True)
    text = page.src_path.read_text(encoding="utf-8", errors="replace")

    display_title = page.title
    if page.is_markdown:
        md_title, body = extract_leading_h1(text)
        if md_title:
            display_title = md_title
        content_html = render_markdown(body)
    else:
        content_html = render_txt(text)

    depth = len(page.out_path.relative_to(OUTPUT_ROOT).parts) - 1
    up = "../" * depth
    css_href = up + "assets/style.css"
    index_href = up + "index.html"

    section_label = humanize_section(page.section)
    if page.group is not None:
        group_label = humanize_group(page.group)
        group_crumb = f'<span class="crumb-sep">/</span><span class="crumb">{html.escape(group_label)}</span>'
        subtitle = f"{html.escape(section_label)} · {html.escape(group_label)}"
    else:
        group_crumb = ""
        subtitle = html.escape(section_label)

    def link(target: Page | None, kind: str) -> str:
        if target is None:
            return f'<a class="{kind} disabled"></a>'
        rel = _rel_link(page, target)
        label = "Previous" if kind == "prev" else "Next"
        arrow_pre = "← " if kind == "prev" else ""
        arrow_post = " →" if kind == "next" else ""
        return (f'<a class="{kind}" href="{html.escape(rel)}">'
                f'<span class="label">{arrow_pre}{label}{arrow_post}</span>'
                f'{html.escape(target.short_title)}</a>')

    html_out = PAGE_TEMPLATE.format(
        title=html.escape(display_title),
        site_title=html.escape(SITE_TITLE),
        css_href=css_href,
        index_href=index_href,
        section=html.escape(section_label),
        group_crumb=group_crumb,
        subtitle=subtitle,
        content=content_html,
        prev_link=link(prev, "prev"),
        next_link=link(nxt, "next"),
    )
    page.out_path.write_text(html_out, encoding="utf-8")


def main() -> None:
    pages = discover_pages()
    if not pages:
        print("No .txt/.md notes found in any topic folder.")
        return
    # prev/next chain runs within each section, in discovery order.
    by_section: dict[str, list[Page]] = {}
    for p in pages:
        by_section.setdefault(p.section, []).append(p)
    written: set[Path] = set()
    for section_pages in by_section.values():
        for i, page in enumerate(section_pages):
            prev = section_pages[i - 1] if i > 0 else None
            nxt = section_pages[i + 1] if i + 1 < len(section_pages) else None
            write_page(page, prev, nxt)
            written.add(page.out_path.resolve())
            print(f"  wrote {page.out_path.relative_to(OUTPUT_ROOT)}")

    index_html = INDEX_TEMPLATE.format(site_title=html.escape(SITE_TITLE), body=build_index(pages))
    index_path = OUTPUT_ROOT / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    written.add(index_path.resolve())

    # Prune stale generated pages (from a renamed / deleted / now-empty note) so a
    # local build matches a clean CI build. Only *.html under topic output dirs is
    # ever removed — assets/ and the tooling scripts are untouched.
    keep_roots = {OUTPUT_ROOT / p.section for p in pages} | {OUTPUT_ROOT}
    for existing in OUTPUT_ROOT.rglob("*.html"):
        if existing.resolve() in written:
            continue
        if any(root in existing.resolve().parents or root == existing.parent for root in keep_roots):
            existing.unlink()
            print(f"  pruned stale {existing.relative_to(OUTPUT_ROOT)}")
    # Disable Jekyll on GitHub Pages so files/folders starting with "_" or "."
    # are served verbatim instead of being silently dropped.
    (OUTPUT_ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"\nGenerated {len(pages)} pages + index.html")


if __name__ == "__main__":
    main()
