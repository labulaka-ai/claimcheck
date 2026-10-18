# -*- coding: utf-8 -*-
"""Run the frozen 40-question set against two systems over the SAME content.
Graph system: deterministic edge traversal of evidence_graph.json (structured lookup).
Vector baseline: naive TF-IDF cosine retrieval over flattened text chunks
(one chunk per paper/claim/evidence/counterexample/method/dataset node).
Scoring: a system scores a question iff its returned chunk id == gold_chunk
(boundary question: returned claim-id set == gold set). This is a first
baseline table, not an embedding-RAG benchmark.
"""
import json, math, pathlib, re
from collections import Counter

here = pathlib.Path(__file__).parent
G = json.loads((here.parent / "build" / "evidence_graph.json").read_text(encoding="utf-8"))
E = json.loads((here / "eval_set.json").read_text(encoding="utf-8"))
papers = {p["id"]: p for p in G["nodes"]["Paper"]}
claims = {c["id"]: c for c in G["nodes"]["Claim"]}
sup, con = {}, {}
for a, rel, b in G["edges"]:
    if rel == "SUPPORTED_BY": sup.setdefault(a, []).append(b)
    elif rel == "CONTRADICTED_BY": con.setdefault(a, []).append(b)

def graph_answer(q):
    if q["type"] == "evidence": return sup[q["claim_id"]][0]
    if q["type"] == "counterexample": return con[q["claim_id"]][0]
    if q["type"] == "attribution": return q["paper_id"]
    if q["type"] == "method": return f"{q['paper_id']}_method"
    if q["type"] == "boundary":
        return {c["id"] for c in claims.values() if c["text"] == "Credibility boundary"}
    return None

chunks = {}
for p in G["nodes"]["Paper"]: chunks[p["id"]] = p["title"] + " " + p["source"]
for c in G["nodes"]["Claim"]: chunks[c["id"]] = c["text"]
for e in G["nodes"]["Evidence"]: chunks[e["id"]] = e["text"]
for e in G["nodes"]["Counterexample"]: chunks[e["id"]] = e["text"]
for m in G["nodes"]["Method"]: chunks[m["id"]] = m["text"]
for d in G["nodes"]["Dataset"]: chunks[d["id"]] = d["text"]

def toks(s): return re.findall(r"[a-z0-9]+", s.lower())
df = Counter()
for t in chunks.values(): df.update(set(toks(t)))
N = len(chunks)
def vec(s):
    c = Counter(toks(s)); v = {}
    for w, k in c.items():
        idf = math.log((N + 1) / (df.get(w, 0) + 1)) + 1
        v[w] = k * idf
    return v
cvecs = {cid: vec(t) for cid, t in chunks.items()}
def cos(a, b):
    dot = sum(a[w] * b.get(w, 0) for w in a)
    na = math.sqrt(sum(x * x for x in a.values())); nb = math.sqrt(sum(x * x for x in b.values()))
    return dot / (na * nb) if na and nb else 0.0
def vector_answer(q):
    if q["type"] == "boundary":
        qv = vec(q["question"])
        ranked = sorted(chunks, key=lambda cid: -cos(qv, cvecs[cid]))
        return {cid for cid in ranked[:6] if chunks[cid] == "Credibility boundary"}
    qv = vec(q["question"])
    return max(chunks, key=lambda cid: cos(qv, cvecs[cid]))

rows = []
for q in E["questions"]:
    g = graph_answer(q); v = vector_answer(q)
    gold = q["gold_chunk"] if q["type"] != "boundary" else {x.strip() for x in q["gold_text"].split(",")}
    rows.append({"id": q["id"], "type": q["type"], "gold": q["gold_chunk"],
                 "graph_hit": g == gold, "vector_hit": v == gold,
                 "vector_got": v if isinstance(v, str) else sorted(v)})
res = {"set": E["set_id"], "n": len(rows),
       "graph_score": sum(r["graph_hit"] for r in rows),
       "vector_score": sum(r["vector_hit"] for r in rows),
       "by_type": {}}
for t in sorted({r["type"] for r in rows}):
    sub = [r for r in rows if r["type"] == t]
    res["by_type"][t] = {"n": len(sub), "graph": sum(r["graph_hit"] for r in sub),
                         "vector": sum(r["vector_hit"] for r in sub)}
(here / "results.json").write_text(json.dumps({"summary": res, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
