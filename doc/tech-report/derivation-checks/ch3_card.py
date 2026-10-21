"""Run a probe on a custom YAML card in a fresh interpreter (kintera's species registry is process-wide).

`run(card_text, probe_src, *args)` writes the card to a temporary file and runs `probe_src` with
`sys.argv[1]` = card path and the remaining args, with the same kintera build as common.py ($KINTERA_WT).
The probe prints one JSON line; the last stdout line that starts with '{' or '[' is returned as a Python object (a
build may print diagnostics after it).
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PRELUDE = ("import sys, json, math\n"
           f"sys.path.insert(0, {HERE!r})\n"
           "from common import kintera, torch\n")


def run(card_text, probe_src, *args):
    d = tempfile.mkdtemp(prefix="ch3_card_")
    card = os.path.join(d, "card.yaml")
    with open(card, "w") as f:
        f.write(card_text)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    res = subprocess.run([sys.executable, "-c", PRELUDE + probe_src, card] + [str(a) for a in args],
                         capture_output=True, text=True, cwd=d, env=env)
    if res.returncode != 0:
        raise RuntimeError(res.stderr[-2000:])
    return json.loads([ln for ln in res.stdout.splitlines() if ln.startswith(("{", "["))][-1])


#: condensate cards that match their saturation curves on the branch where each test cloud forms (C3-g step 3;
#: the values of the K8 fix): cv_R and u0_R at Tref = 300 K
FIXED = {"H2O(l)": (8.486009, -4990.8575), "NH3(s)": (4.93, -3304.056)}


def fixed_deck(deck):
    out, cur = [], None
    for line in deck.splitlines():
        s = line.strip()
        if s.startswith("- name:"):
            cur = s.split(":", 1)[1].strip()
        if cur in FIXED and s.startswith("cv_R:"):
            line = line.split("cv_R:")[0] + f"cv_R: {FIXED[cur][0]}"
        if cur in FIXED and s.startswith("u0_R:"):
            line = line.split("u0_R:")[0] + f"u0_R: {FIXED[cur][1]}"
        out.append(line)
    return "\n".join(out) + "\n"
