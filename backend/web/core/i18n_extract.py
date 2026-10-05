"""Collects the web surfaces' translatable strings without GNU gettext
(xgettext isn't installed in the image; see DECISIONS.md "Translations
without GNU gettext"). Mirrors Django's makemessages normalisation for the
forms used here: {% translate "…" %}, {% blocktranslate [trimmed] [with …]
[count …] %}…{% plural %}…{% endblocktranslate %}, and _()/gettext()/
gettext_lazy()/ngettext() string literals in web/**/*.py."""
import ast
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent

_TRANS = re.compile(r"""\{%\s*(?:translate|trans)\s+(?P<q>["'])(?P<s>.*?)(?P=q)(?:\s+[^%]*)?%\}""", re.S)
_BLOCK = re.compile(r"\{%\s*(?:blocktranslate|blocktrans)(?P<opts>[^%]*)%\}(?P<body>.*?)\{%\s*(?:endblocktranslate|endblocktrans)\s*%\}", re.S)
_VAR = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")
_FILTER_ARG = re.compile(r"""_\((?P<q>["'])(?P<s>.*?)(?P=q)\)""")


def _block_msgid(text, trimmed):
    text = _VAR.sub(lambda m: f"%({m.group(1)})s", text.replace("%", "%%").replace("%%(", "%("))
    if trimmed:
        text = " ".join(line.strip() for line in text.strip().splitlines() if line.strip())
    return text


def from_templates():
    out = {}
    for path in sorted(WEB.rglob("*.html")):
        src = path.read_text(encoding="utf-8")
        for m in _TRANS.finditer(src):
            out.setdefault(m.group("s"), None)
        for m in _BLOCK.finditer(src):
            trimmed = "trimmed" in m.group("opts")
            body = m.group("body")
            if re.search(r"\{%\s*plural\s*%\}", body):
                singular, plural = re.split(r"\{%\s*plural\s*%\}", body)
                out.setdefault(_block_msgid(singular, trimmed), _block_msgid(plural, trimmed))
            else:
                out.setdefault(_block_msgid(body, trimmed), None)
        for m in _FILTER_ARG.finditer(src):
            out.setdefault(m.group("s"), None)
    return out


def from_python():
    out = {}
    names = {"_", "gettext", "gettext_lazy", "ngettext", "ngettext_lazy"}
    for path in sorted(WEB.rglob("*.py")):
        if "tests" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) in names and node.args:
                args = [a.value for a in node.args[:2] if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                if args:
                    out.setdefault(args[0], args[1] if node.func.id.startswith("ngettext") and len(args) > 1 else None)
    return out


def web_msgids():
    """{msgid: msgid_plural or None}, sorted."""
    found = {**from_python(), **from_templates()}
    return dict(sorted(found.items()))
