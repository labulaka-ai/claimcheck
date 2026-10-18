# live verify run 2026-10-18T07:42:52 host=127.0.0.1 port=6399
existing evidence_graph deleted for clean ingest
ingest statements: 84 (skipped 2 legacy CREATE CONSTRAINT: FalkorDB 6.0 wants GRAPH.CONSTRAINT; ids are unique by construction in the verified JSON)
ingest done
nodes Paper: live=3 expected=3 OK
nodes Claim: live=12 expected=12 OK
nodes Evidence: live=12 expected=12 OK
nodes Counterexample: live=12 expected=12 OK
nodes Method: live=3 expected=3 OK
nodes Dataset: live=3 expected=3 OK
edges: live=39 expected=39 OK

== eval sample on LIVE engine ==
Q01 [evidence] claim=fire_c1 -> PASS
Q02 [counterexample] claim=fire_c1 -> PASS
Q03 [attribution] claim=fire_c1 -> PASS
Q04 [evidence] claim=fire_c2 -> PASS
Q05 [counterexample] claim=fire_c2 -> PASS
Q37 [method] claim=None -> PASS
sample result: 6/6 pass; counts_ok=True
