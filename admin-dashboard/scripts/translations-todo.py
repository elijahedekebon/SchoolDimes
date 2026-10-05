"""Regenerates the dashboard part of docs/TRANSLATIONS_TODO.md: every key in
messages/en.json that messages/lg.json or messages/sw.json lacks."""
import json
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent
en = json.load(open(root / "messages/en.json"))


def flat(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            yield from flat(v, key + ".")
        else:
            yield key, v


en_keys = dict(flat(en))
lines = []
for lang in ("lg", "sw"):
    have = dict(flat(json.load(open(root / f"messages/{lang}.json"))))
    missing = [k for k in en_keys if k not in have]
    lines.append(f"### `admin-dashboard/messages/{lang}.json` — {len(missing)} of {len(en_keys)} keys missing\n")
    if len(missing) == len(en_keys):
        lines.append("All keys (the file is empty; English is shown). The English source is in `messages/en.json`.\n")
    else:
        lines += [f"- `{k}`" for k in missing] + [""]
out = root.parent / "docs/TRANSLATIONS_TODO.md"
text = out.read_text() if out.exists() else ""
start, end = "<!-- dashboard:start -->", "<!-- dashboard:end -->"
block = start + "\n" + "\n".join(lines) + "\n" + "\n".join(f"<details><summary>{n}</summary>\n\n" + "\n".join(
    f"- `{k}`: {v}" for k, v in en_keys.items() if k.split('.')[0] == n) + "\n</details>\n" for n in en) + end
if start in text:
    text = text[: text.index(start)] + block + text[text.index(end) + len(end):]
else:
    text += "\n" + block + "\n"
out.write_text(text)
print(f"{len(en_keys)} dashboard keys listed")
