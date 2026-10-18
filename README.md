# ClaimCheck — an evidence graph that answers "should I trust this claim?"

Built for **Graph Hacks 2026** (WeMakeDevs × FalkorDB) — tracks: **Company Brain** and **Agents That Act on Connected Data**.

ClaimCheck is a small evidence graph over three verified climate-AI papers. Every claim in the graph carries the two things most RAG demos omit:

1. the **evidence** that supports it, and
2. the **counterexample or scope limit** that bounds it.

Ask about a claim and the answer walks the graph: paper → claim → supporting evidence → contradicting evidence or stated limits. Where the source pack has no real counter-result, the node says so explicitly — *"scope limit (not a counter-result)"* — instead of inventing one.

## The graph

| | Count |
|---|---|
| Papers | 3 |
| Claims | 12 |
| Evidence | 12 |
| Counterexamples / scope limits | 12 |
| Methods | 3 |
| Datasets | 3 |
| Edges | 39 |

Papers: a global fire-forecast GNN paper (arXiv:2610.11022), CLARA joint probabilistic forecasting (arXiv:2610.09898), and a GraphCast mechanistic-interpretability paper (arXiv:2610.07583). All numbers in the pack were verified against the papers before the event; the pack itself is `evidence-data-pack-v1.md`.

Schema: `Paper -TESTED_BY-> Method`, `Claim -SUPPORTED_BY-> Evidence`, `Claim -CONTRADICTED_BY-> Counterexample`, `Evidence -DERIVED_FROM-> Dataset`. Attribution is the `Claim.paper` property.

## Run it

Prerequisite: Docker, Python 3.10+.

```bash
# 1. Start FalkorDB 6.0.0 (pinned — do not float on latest)
docker run -d --name claimcheck -p 6399:6379 falkordb/falkordb:6.0.0

# 2. Install the client
pip install falkordb

# 3. Ingest the graph and verify it live (counts + eval sample)
python3 live_verify.py --port 6399

# 4. Answer all 40 frozen eval questions by live graph traversal
python3 live_eval_full.py

# 5. Offline Q&A (same graph shape, no server needed)
python3 qa.py --list
python3 qa.py fire
```

`build_graph.py` regenerates `evidence_graph.json` and `ingest.cypher` from `evidence-data-pack-v1.md` — the JSON, the Cypher and the pack cannot drift apart without the builder's self-check failing.

Note: the two legacy `CREATE CONSTRAINT` statements at the top of `ingest.cypher` are skipped by `live_verify.py` (FalkorDB 6.0 uses the `GRAPH.CONSTRAINT` command instead); node ids are unique by construction in the verified pack.

## Evaluation

`eval/eval_set.json` is a **frozen 40-question set** (evidence 12, counterexample/boundary 12, attribution 12, method 3, trust-boundary 1), generated only from the verified graph. Three systems, same questions:

| System | Score | Honest reading |
|---|---|---|
| Graph traversal (this project) | 40/40 | Sanity proof that graph and eval agree — questions and gold answers come from the same verified graph. **Not** an independent performance claim. |
| TF-IDF, claim-anchored chunks | 32/40 | Fails mostly on evidence-vs-counterexample confusion. |
| TF-IDF, flat chunks (naive RAG) | 1/40 | The honest failure: questions quote claim text verbatim, so flat retrieval surfaces the claim chunk itself and the evidence chunks never rank. Chunking design, not model quality, breaks naive RAG here. |

Live-engine run (2026-10-18, FalkorDB 6.0.0, image digest `sha256:92fbda814970…`): ingest counts matched the JSON exactly (3/12/12/12/3/3 nodes, 39 edges). All 40 questions were then answered against the **live** graph: 39/40 through the per-question traversal harness, and the remaining set-valued boundary question (Q40) verified with a set query returning exactly the gold set `{clara_c4, fire_c4, gc_c4}`. Logs: `live_verify_log.md`, and the full-run log is produced by `live_eval_full.py`.

## What this is for

Pre-submission checking of scientific claims: before a claim goes into a paper, a report, or a post, walk its evidence and its limits. The same pack is being reused as the verification set for a paper-audit workflow.

## Limitations

- Three papers, 45 nodes — a depth-first proof, not a corpus. The builder generalizes to any pack written in the same format.
- The baselines are TF-IDF, not embedding retrieval; no cross-team score comparisons are made or implied.
- No live deployment; local setup above is the supported path.

## Files

- `evidence-data-pack-v1.md` — the verified source pack (claims, evidence, limits, with sources)
- `build_graph.py` — pack → `evidence_graph.json` + `ingest.cypher`, with self-checks
- `qa.py` — offline Q&A over the JSON graph
- `live_verify.py` / `live_eval_full.py` — ingest + verification against a running FalkorDB
- `eval/` — frozen question set, generators, baseline runners and results

MIT licensed. Built by Labulaka, solo, during Graph Hacks (Oct 15–19, 2026). Coding assistants were used, as the event rules allow; every number above is traceable to the verified pack or to a run log in this repo.
