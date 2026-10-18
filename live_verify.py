# -*- coding: utf-8 -*-
"""S69 live-engine verification: ingest ingest.cypher into a running FalkorDB
(port 6399, graph 'evidence_graph'), check node/edge counts against
evidence_graph.json, then answer a sample of frozen eval questions by real
graph traversal and compare against gold text.

Usage: python3 live_verify.py [--host 127.0.0.1] [--port 6399]
Requires: pip install falkordb
Writes: live_verify_log.md next to this script.
"""
import json, pathlib, sys, datetime

HERE = pathlib.Path(__file__).parent
HOST = "127.0.0.1"
PORT = 6399
if "--port" in sys.argv:
    PORT = int(sys.argv[sys.argv.index("--port") + 1])
if "--host" in sys.argv:
    HOST = sys.argv[sys.argv.index("--host") + 1]

from falkordb import FalkorDB

log = []
def say(s=""):
    print(s)
    log.append(s)

db = FalkorDB(host=HOST, port=PORT)
g = db.select_graph("evidence_graph")

# clean slate so counts are exact
try:
    g.delete()
    say("existing evidence_graph deleted for clean ingest")
except Exception:
    pass
g = db.select_graph("evidence_graph")

# --- ingest ---
cypher = (HERE / "ingest.cypher").read_text(encoding="utf-8")
stmts = []
for chunk in cypher.split(";\n"):
    lines = [ln for ln in chunk.splitlines() if ln.strip() and not ln.strip().startswith("//")]
    s = "\n".join(lines).strip()
    if s:
        stmts.append(s)
skipped = [s for s in stmts if s.upper().startswith("CREATE CONSTRAINT")]
stmts = [s for s in stmts if not s.upper().startswith("CREATE CONSTRAINT")]
say(f"ingest statements: {len(stmts)} (skipped {len(skipped)} legacy CREATE CONSTRAINT: "
    "FalkorDB 6.0 wants GRAPH.CONSTRAINT; ids are unique by construction in the verified JSON)")
for s in stmts:
    g.query(s)
say("ingest done")

# --- counts vs JSON ---
G = json.loads((HERE / "evidence_graph.json").read_text(encoding="utf-8"))
exp_nodes = {k: len(v) for k, v in G["nodes"].items()}
exp_edges = len(G["edges"])
ok = True
for label, exp in exp_nodes.items():
    got = list(g.query(f"MATCH (n:{label}) RETURN count(n)").result_set)[0][0]
    flag = "OK" if got == exp else "MISMATCH"
    if got != exp:
        ok = False
    say(f"nodes {label}: live={got} expected={exp} {flag}")
got_edges = list(g.query("MATCH ()-[r]->() RETURN count(r)").result_set)[0][0]
say(f"edges: live={got_edges} expected={exp_edges} {'OK' if got_edges == exp_edges else 'MISMATCH'}")
if got_edges != exp_edges:
    ok = False

# --- eval sample by graph traversal ---
ev = json.loads((HERE.parent / "eval-20261017" / "eval_set.json").read_text(encoding="utf-8"))
qs = {q["id"]: q for q in ev["questions"]}
sample_ids = ["Q01", "Q02", "Q03", "Q04", "Q05", "Q37"]
say("")
say("== eval sample on LIVE engine ==")
passed = 0
for qid in sample_ids:
    q = qs[qid]
    t = q["type"]
    if t == "evidence":
        rows = list(g.query(
            "MATCH (c:Claim {id:$cid})-[:SUPPORTED_BY]->(e:Evidence) RETURN e.text",
            {"cid": q["claim_id"]}).result_set)
        got = rows[0][0] if rows else ""
    elif t == "counterexample":
        rows = list(g.query(
            "MATCH (c:Claim {id:$cid})-[:CONTRADICTED_BY]->(x:Counterexample) RETURN x.text",
            {"cid": q["claim_id"]}).result_set)
        got = rows[0][0] if rows else ""
    elif t == "attribution":
        # graph models attribution as Claim.paper property (no Claim->Paper edge)
        rows = list(g.query(
            "MATCH (c:Claim {id:$cid}) RETURN c.paper",
            {"cid": q["claim_id"]}).result_set)
        pid = rows[0][0] if rows else ""
        rows = list(g.query(
            "MATCH (p:Paper {id:$pid}) RETURN p.source",
            {"pid": pid}).result_set)
        got = rows[0][0] if rows else ""
    elif t == "method":
        rows = list(g.query(
            "MATCH (m:Method {id:$mid}) RETURN m.text",
            {"mid": q["gold_chunk"]}).result_set)
        got = rows[0][0] if rows else ""
    else:
        got = ""
    match = (got.strip() == q["gold_text"].strip())
    passed += match
    say(f"{qid} [{t}] claim={q.get('claim_id')} -> {'PASS' if match else 'FAIL'}")
    if not match:
        say(f"  gold: {q['gold_text'][:120]}")
        say(f"  got : {str(got)[:120]}")
say(f"sample result: {passed}/{len(sample_ids)} pass; counts_ok={ok}")

hdr = f"# live verify run {datetime.datetime.now().isoformat(timespec='seconds')} host={HOST} port={PORT}\n"
(HERE / "live_verify_log.md").write_text(hdr + "\n".join(log) + "\n", encoding="utf-8")
sys.exit(0 if (ok and passed == len(sample_ids)) else 1)
