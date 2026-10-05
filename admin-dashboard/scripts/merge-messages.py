"""Merges a JSON fragment (stdin) into messages/en.json. Dev helper."""
import json, sys
path = "messages/en.json"
base = json.load(open(path))
frag = json.load(sys.stdin)
def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            merge(a[k], v)
        else:
            a[k] = v
merge(base, frag)
json.dump(base, open(path, "w"), indent=2, ensure_ascii=False)
open(path, "a").write("\n")
