# -*- coding: utf-8 -*-
"""Freeze a 40-question evaluation set from the verified S69 evidence graph.
Every question and gold answer is derived only from evidence_graph.json
(12 claims x evidence/counterexample/attribution = 36, + 3 method + 1 boundary = 40).
No numbers or texts are invented; gold answers are verbatim graph fields.
"""
import json, pathlib, hashlib

here = pathlib.Path(__file__).parent
G = json.loads((here.parent / "build" / "evidence_graph.json").read_text(encoding="utf-8"))
papers = {p["id"]: p for p in G["nodes"]["Paper"]}
claims = G["nodes"]["Claim"]
ev = {e["id"]: e["text"] for e in G["nodes"]["Evidence"]}
cx = {e["id"]: e["text"] for e in G["nodes"]["Counterexample"]}
methods = {m["id"]: m["text"] for m in G["nodes"]["Method"]}
sup, con = {}, {}
for a, rel, b in G["edges"]:
    if rel == "SUPPORTED_BY":
        sup.setdefault(a, []).append(b)
    elif rel == "CONTRADICTED_BY":
        con.setdefault(a, []).append(b)

qs = []
n = 0
def add(qtype, question, gold_chunk, gold_text, claim_id=None, paper_id=None):
    global n
    n += 1
    qs.append({"id": f"Q{n:02d}", "type": qtype, "question": question,
               "gold_chunk": gold_chunk, "gold_text": gold_text,
               "claim_id": claim_id, "paper_id": paper_id})

for c in claims:
    cid, pid = c["id"], c["paper"]
    eid = sup[cid][0]; xid = con[cid][0]
    add("evidence", f"What evidence supports this claim: \"{c['text']}\" (paper {papers[pid]['source']})?",
        eid, ev[eid], cid, pid)
    add("counterexample", f"What is the counterexample or limit for this claim: \"{c['text']}\" (paper {papers[pid]['source']})?",
        xid, cx[xid], cid, pid)
    add("attribution", f"Which paper does this claim come from: \"{c['text']}\"? Give the paper source id.",
        pid, papers[pid]["source"], cid, pid)

for pid, p in papers.items():
    mid = f"{pid}_method"
    add("method", f"What method was used in the paper {p['source']} (\"{p['title']}\")?",
        mid, methods[mid], None, pid)

boundary = [c["id"] for c in claims if c["text"] == "Credibility boundary"]
add("boundary", "Which claims in the pack are the papers' own credibility-boundary claims? List their claim ids.",
    "boundary_set", ", ".join(boundary), None, None)

assert len(qs) == 40, len(qs)
out = {"set_id": "s69-eval-v1-20261017", "source_graph": "build/evidence_graph.json",
       "n_questions": 40, "questions": qs}
text = json.dumps(out, ensure_ascii=False, indent=1)
(here / "eval_set.json").write_text(text, encoding="utf-8")
print("questions:", len(qs), "| sha256:", hashlib.sha256(text.encode()).hexdigest()[:16])
from collections import Counter
print(Counter(q["type"] for q in qs))
