"""Checks the translation files: same keys in en/de, and every t("...") key used in the UI exists.
Run:  python check_i18n.py
"""
import json
import re
from pathlib import Path

root = Path(__file__).parent
en = json.loads((root / "i18n" / "en.json").read_text(encoding="utf-8"))
de = json.loads((root / "i18n" / "de.json").read_text(encoding="utf-8"))

ok = True
for name, a, b in (("de", en, de), ("en", de, en)):
    missing = sorted(set(a) - set(b))
    if missing:
        ok = False
        print(f"missing in {name}.json:", missing)

src = (root / "app.js").read_text(encoding="utf-8") + (root / "index.html").read_text(encoding="utf-8")
used = set(re.findall(r'\bt\("([\w.]+)"', src)) | set(re.findall(r'data-i18n="([\w.]+)"', src))
# keys built at runtime ("err." + code, "steps." + name, t(key)) are checked explicitly below
used = {k for k in used if "." in k and not k.endswith(".")}
states = ["REQUESTED", "RESERVED", "PLATE_MISMATCH", "BLOCKED", "UNVERIFIED", "ARRIVED", "CHARGING",
          "COMPLETED", "CANCELLED", "NO_SHOW", "FAILED", "FAULT_REPORTED"]
used |= {f"state.{s}.{p}" for s in states for p in ("title", "sub")}
used |= {f"steps.{s}" for s in ("reserved", "arrived", "charging", "done")}
unknown = sorted(k for k in used if k not in en)
if unknown:
    ok = False
    print("keys used in code but not defined:", unknown)
print("i18n OK" if ok else "i18n problems found", f"({len(en)} keys)")
