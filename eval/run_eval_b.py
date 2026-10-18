# -*- coding: utf-8 -*-
"""Variant B baseline: standard claim-anchored RAG chunking.
Each evidence/counterexample chunk is prefixed with its claim text (how flat
RAG corpora are normally built); pure claim chunks are not candidates.
Method chunks are prefixed with paper title+source; attribution candidates
are per-paper combined chunks (title+source+all claim texts).
Same TF-IDF cosine retriever and same gold-chunk scoring as run_eval.py.
"""
import json, math, pathlib, re
from collections import Counter

here = pathlib.Path(__file__).parent
G = json.loads((here.parent / "build" / "evidence_graph.json").read_text(encoding="utf-8"))
E = json.loads((here / "eval_set.json").read_text(encoding="utf-8"))
papers = {p["id"]: p for p in G["nodes"]["Paper"]}
claims = {c["id"]: c for c in G["nodes"]["Claim"]}
claim_of_ev, claim_of_cx = {}, {}
for a, rel, b in G["edges"]:
    if rel == "SUPPORTED_BY": claim_of_ev[b] = a
    elif rel == "CONTRADICTED_BY": claim_of_cx[b] = a

chunks = {}
for e in G["nodes"]["Evidence"]:
    chunks[e["id"]] = claims[claim_of_ev[e["id"]]]["text"] + " " + e["text"]
for e in G["nodes"]["Counterexample"]:
    chunks[e["id"]] = claims[claim_of_cx[e["id"]]]["text"] + " " + e["text"]
for m in G["nodes"]["Method"]:
    pid = m["id"].replace("_method", "")
    chunks[m["id"]] = papers[pid]["title"] + " " + papers[pid]["source"] + " " + m["text"]
for pid, p in papers.items():
    own = " ".join(c["text"] for c in claims.values() if c["paper"] == pid)
    chunks[pid] = p["title"] + " " + p["source"] + " " + own

def toks(s): return re.findall(r"[a-z0-9]+", s.lower())
df = Counter()
for t in chunks.values(): df.update(set(toks(t)))
N = len(chunks)
def vec(s):
    return {w: k * (math.log((N + 1) / (df.get(w, 0) + 1)) + 1) for w, k in Counter(toks(s)).items()}
cvecs = {cid: vec(t) for cid, t in chunks.items()}
def cos(a, b):
    dot = sum(a[w] * b.get(w, 0) for w in a)
    na = math.sqrt(sum(x * x for x in a.values())); nb = math.sqrt(sum(x * x for x in b.values()))
    return dot / (na * nb) if na and nb else 0.0

rows = []
for q in E["questions"]:
    if q["type"] == "boundary":
        got = {cid for cid, t in chunks.items() if t.split(" ")[0] and cid in claims and claims[cid]["text"] == "Credibility boundary"}
        # boundary has no chunk in variant B corpus; mark as not-applicable -> count as miss, flagged
        rows.append({"id": q["id"], "type": q["type"], "hit": False, "note": "no boundary chunk in flat corpus"})
        continue
    cand = [cid for cid in chunks if cid == q["gold_chunk"]]  # placeholder, replaced below
    if q["type"] in ("evidence", "counterexample"):
        cand = [e["id"] for e in (G["nodes"]["Evidence"] if q["type"] == "evidence" else G["nodes"]["Counterexample"])]
    elif q["type"] == "attribution":
        cand = list(papers)
    elif q["type"] == "method":
        cand = [m["id"] for m in G["nodes"]["Method"]]
    qv = vec(q["question"])
    got = max(cand, key=lambda cid: cos(qv, cvecs[cid]))
    rows.append({"id": q["id"], "type": q["type"], "hit": got == q["gold_chunk"], "got": got})

res = {"variant": "B claim-anchored TF-IDF, candidates restricted to gold type",
       "n": len(rows), "score": sum(r["hit"] for r in rows), "by_type": {}}
for t in sorted({r["type"] for r in rows}):
    sub = [r for r in rows if r["type"] == t]
    res["by_type"][t] = {"n": len(sub), "hits": sum(r["hit"] for r in sub)}
(here / "results_b.json").write_text(json.dumps({"summary": res, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
