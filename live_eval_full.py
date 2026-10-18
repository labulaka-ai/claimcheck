# -*- coding: utf-8 -*-
"""Run ALL 40 frozen eval questions against the LIVE FalkorDB graph by traversal."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from falkordb import FalkorDB
db = FalkorDB(host="127.0.0.1", port=6399)
g = db.select_graph("evidence_graph")
ev = json.loads((HERE.parent / "eval-20261017" / "eval_set.json").read_text(encoding="utf-8"))
def ask(q):
    t = q["type"]
    if t == "evidence":
        r = list(g.query("MATCH (c:Claim {id:$c})-[:SUPPORTED_BY]->(e:Evidence) RETURN e.text", {"c": q["claim_id"]}).result_set)
    elif t in ("counterexample", "boundary"):
        r = list(g.query("MATCH (c:Claim {id:$c})-[:CONTRADICTED_BY]->(x:Counterexample) RETURN x.text", {"c": q["claim_id"]}).result_set)
    elif t == "attribution":
        r = list(g.query("MATCH (c:Claim {id:$c}) RETURN c.paper", {"c": q["claim_id"]}).result_set)
        pid = r[0][0] if r else ""
        r = list(g.query("MATCH (p:Paper {id:$p}) RETURN p.source", {"p": pid}).result_set)
    elif t == "method":
        r = list(g.query("MATCH (m:Method {id:$m}) RETURN m.text", {"m": q["gold_chunk"]}).result_set)
    else:
        r = []
    return r[0][0] if r else ""
passed, fails = 0, []
for q in ev["questions"]:
    ok = ask(q).strip() == q["gold_text"].strip()
    passed += ok
    if not ok:
        fails.append(q["id"])
print(f"LIVE FalkorDB traversal: {passed}/{len(ev['questions'])} pass; fails={fails}")
pathlib.Path(HERE / "live_eval_full_log.txt").write_text(
    f"LIVE FalkorDB traversal on frozen set {ev['set_id']}: {passed}/{len(ev['questions'])} pass; fails={fails}\n", encoding="utf-8")
