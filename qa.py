# -*- coding: utf-8 -*-
"""S69 QA skeleton: answers 'is this claim reliable, where is the evidence,
what is the counterexample' by walking evidence_graph.json.
Works fully offline (in-memory fallback); if FalkorDB is reachable the same
graph shape is what ingest.cypher loads, so answers stay identical.
Usage: python3 qa.py "fire"  |  python3 qa.py --list
"""
import json, pathlib, sys

G = json.loads((pathlib.Path(__file__).parent / "evidence_graph.json").read_text(encoding="utf-8"))
claims = {c["id"]: c for c in G["nodes"]["Claim"]}
papers = {p["id"]: p for p in G["nodes"]["Paper"]}
ev = {e["id"]: e["text"] for e in G["nodes"]["Evidence"]}
cx = {e["id"]: e["text"] for e in G["nodes"]["Counterexample"]}
sup, con = {}, {}
for a, rel, b in G["edges"]:
    if rel == "SUPPORTED_BY":
        sup.setdefault(a, []).append(ev[b])
    elif rel == "CONTRADICTED_BY":
        con.setdefault(a, []).append(cx[b])

def answer(cid):
    c = claims[cid]
    p = papers[c["paper"]]
    out = [f"Paper: {p['title']} ({p['source']})", f"Claim: {c['text']}", "Evidence:"]
    out += [f"  - {t}" for t in sup.get(cid, ["(none recorded)"])]
    out.append("Counterexample / limits:")
    out += [f"  - {t}" for t in con.get(cid, ["(none in pack - flagged, do not present as fully checked)"])]
    return "\n".join(out)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--list":
        for cid, c in claims.items():
            print(cid, "|", papers[c["paper"]]["source"], "|", c["text"])
    else:
        q = sys.argv[1].lower()
        hits = [cid for cid, c in claims.items() if q in cid or q in c["text"].lower()]
        print("\n\n".join(answer(h) for h in hits) if hits else "no claim matched")
