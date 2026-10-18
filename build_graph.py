# -*- coding: utf-8 -*-
"""S69 evidence graph builder.
Extracts the verified evidence pack (evidence-data-pack-v1.md, 2026-10-12)
into structured JSON + FalkorDB Cypher ingest script, with offline checks.
All numbers are copied from the pack; nothing is re-derived.
"""
import json, pathlib

OUT = pathlib.Path(__file__).parent

PAPERS = [
    {
        "id": "fire_gnn",
        "title": "A Graph Neural Network for Global Daily Fire Radiative Power Prediction at Medium-Range Lead Times",
        "authors": "Li Zhang, Jun Wang, Isidora Jankov et al. (NOAA / CU Boulder)",
        "source": "arXiv:2610.11022",
        "method": "Spatiotemporal GNN (grid cells linked by geographic proximity); inputs: historical fire points + reanalysis meteorology + land cover/vegetation; trained 2020-2022, fully held-out test 2023 and 2024; baseline: operational persistence forecast.",
        "dataset": "GBBEPx satellite fire radiative power (FRP) product",
        "claims": [
            {
                "id": "fire_c1",
                "text": "7-day-ahead global fire forecast error is significantly below the operational persistence forecast",
                "evidence": ["0.1deg MSE: 2023 lead-1 -32%, lead-7 -43%; 2024 -24% and -40% vs persistence"],
                "counter": ["The advantage grows with lead time because the 'no-change' assumption degrades faster - it does not mean high absolute 7-day accuracy"],
            },
            {
                "id": "fire_c2",
                "text": "Operational fire-source data is severely stale",
                "evidence": ["Satellite fire product has ~1.5 day latency and is then frozen unchanged through the following 5 days of operational forecasts (7 days frozen in the experimental version)"],
                "counter": ["Scope limit (not a counter-result): the staleness described covers one operational chain only - NOAA GEFS-Aerosols initialised from GBBEPx; fire inputs at other centres are outside this claim's coverage"],
            },
            {
                "id": "fire_c3",
                "text": "Large-fire locations are reliable",
                "evidence": ["1deg fire-detection critical success index 0.32-0.60, decaying only slowly with lead time"],
                "counter": ["Large-fire radiative power is systematically underestimated; small-fire locations are often wrong - intensity calibration and small-fire localisation are the authors' own two 'lessons before deployment'"],
            },
            {
                "id": "fire_c4",
                "text": "Credibility boundary",
                "evidence": ["Training and testing both use the GBBEPx product definition"],
                "counter": ["Real operational observation noise and product version changes not covered; preprint, not peer-reviewed"],
            },
        ],
    },
    {
        "id": "clara",
        "title": "Learning joint probabilistic weather forecasts from station observations alone (CLARA)",
        "authors": "Chaeyeon Yi, Yun Am Seo (HUFS / Jeju National University)",
        "source": "arXiv:2610.09898",
        "method": "Wind-direction-biased attention (upwind positions back-tracked by lead time, weights decay with lead) + five-variable joint Gaussian output; station observations only, no NWP or reanalysis inputs.",
        "dataset": "Korean automatic weather station system, 96 stations; lead times 1-48h in six bands",
        "claims": [
            {
                "id": "clara_c1",
                "text": "A tiny model can produce joint probabilistic forecasts",
                "evidence": ["~28k parameters; trains 40 epochs in 2.1 min on a regular CPU; one 96-station forecast takes 0.43 ms"],
                "counter": ["Scope limit (not a counter-result): validated only at the scale of 96 stations, 1-48 h leads and five variables; no evidence in this paper at operational grid scale"],
            },
            {
                "id": "clara_c2",
                "text": "Generalisation is stable across regions",
                "evidence": ["Retrained in 10 regions on six continents: wins all 60 region-lead comparisons vs persistence, 57 vs same-scale learning models; energy score 4.9% below same-input rivals, 11%-65% below statistical baselines"],
                "counter": ["Wins are against persistence and same-scale baselines; never faced an operational-grade NWP system head-on"],
            },
            {
                "id": "clara_c3",
                "text": "Inter-variable correlation is real information, not decoration",
                "evidence": ["Ablation: removing learned correlations (variance only) worsens joint-forecast negative log-likelihood by 1.0-2.8 per station"],
                "counter": ["Authors' own caveat: attention bias coefficients cannot be read directly as causal evidence of which station influenced a forecast"],
            },
            {
                "id": "clara_c4",
                "text": "Credibility boundary",
                "evidence": ["Consistency proof exists for the covariance scale estimator"],
                "counter": ["At long leads the proof's premises break first, causing over-correction; joint distribution assumes Gaussianity, extreme tails (where compound disasters live) may be poorly described; preprint"],
            },
        ],
    },
    {
        "id": "graphcast_xai",
        "title": "Mechanistic Interpretability of Atmospheric Rivers in GraphCast",
        "authors": "Madelyn Mathai et al. (University of Virginia)",
        "source": "arXiv:2610.07583; code: github.com/AikyamLab/climate_xai",
        "method": "Sparse autoencoders (Matryoshka variant) fitted at GraphCast processor layers 0/8/15 as a 'concept dictionary' (512-dim activations -> 4096 entries); concepts matched against real atmospheric phenomena, with internal activation interventions to test causality.",
        "dataset": "GraphCast internal activations vs atmospheric river phenomena and IVT (integrated vapour transport) diagnostics",
        "claims": [
            {
                "id": "gc_c1",
                "text": "Nobody taught it IVT, yet GraphCast internally computes it stably",
                "evidence": ["IVT never appears as input or forecast target, yet is stably detected in internal activations; concepts persist across processor depths"],
                "counter": ["Correlation 0.51 evidences that the concept is detected, not the model's computational precision for IVT"],
            },
            {
                "id": "gc_c2",
                "text": "The strongest concept tracks atmospheric river intensity",
                "evidence": ["Concept 99 'global atmospheric river' correlates 0.51 (time-mean) with regional maximum IVT; concept 1592 responds specifically to strong North-American west-coast IVT; concepts form a parent-child hierarchy (99 is a parent)"],
                "counter": ["Scope limit (not a counter-result): the time-mean correlation is 0.51, so a single strongest concept still leaves most IVT variance unexplained; responses are regional (concept 1592 is specific to strong North-American west-coast IVT)"],
            },
            {
                "id": "gc_c3",
                "text": "The concepts are actually used by the model, not bystander correlations",
                "evidence": ["Directly intervening on internal activations changes the forecast accordingly"],
                "counter": ["Intervention evidence is complete only for the atmospheric-river phenomenon class"],
            },
            {
                "id": "gc_c4",
                "text": "Credibility boundary",
                "evidence": ["Code is open source and reproducible"],
                "counter": ["Fully validated only on atmospheric rivers; fronts, blocking highs and other phenomena unverified; preprint"],
            },
        ],
    },
]

def build():
    nodes = {"Paper": [], "Claim": [], "Evidence": [], "Counterexample": [], "Method": [], "Dataset": []}
    edges = []
    problems = []
    for p in PAPERS:
        nodes["Paper"].append({"id": p["id"], "title": p["title"], "authors": p["authors"], "source": p["source"]})
        nodes["Method"].append({"id": p["id"] + "_method", "text": p["method"]})
        nodes["Dataset"].append({"id": p["id"] + "_data", "text": p["dataset"]})
        edges.append((p["id"], "TESTED_BY", p["id"] + "_method"))
        for c in p["claims"]:
            nodes["Claim"].append({"id": c["id"], "paper": p["id"], "text": c["text"]})
            if not c["evidence"]:
                problems.append(f"{c['id']}: NO evidence")
            if not c["counter"]:
                problems.append(f"{c['id']}: NO counterexample (pack cell was '--')")
            for i, e in enumerate(c["evidence"]):
                eid = f"{c['id']}_ev{i+1}"
                nodes["Evidence"].append({"id": eid, "text": e})
                edges.append((c["id"], "SUPPORTED_BY", eid))
                edges.append((eid, "DERIVED_FROM", p["id"] + "_data"))
            for i, x in enumerate(c["counter"]):
                xid = f"{c['id']}_cx{i+1}"
                nodes["Counterexample"].append({"id": xid, "text": x})
                edges.append((c["id"], "CONTRADICTED_BY", xid))
    return nodes, edges, problems

def esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")

def cypher(nodes, edges):
    lines = ["// S69 FalkorDB ingest - generated by build_graph.py from evidence-data-pack-v1.md",
             "CREATE CONSTRAINT ON (p:Paper) ASSERT p.id IS UNIQUE;",
             "CREATE CONSTRAINT ON (c:Claim) ASSERT c.id IS UNIQUE;"]
    label_of = {}
    for label, items in nodes.items():
        for n in items:
            label_of[n["id"]] = label
            props = ", ".join(f"{k}: '{esc(str(v))}'" for k, v in n.items())
            lines.append(f"CREATE (:{label} {{{props}}});")
    for a, rel, b in edges:
        la, lb = label_of[a], label_of[b]
        lines.append(f"MATCH (a:{la} {{id: '{a}'}}), (b:{lb} {{id: '{b}'}}) CREATE (a)-[:{rel}]->(b);")
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    nodes, edges, problems = build()
    graph = {"nodes": nodes, "edges": [list(e) for e in edges]}
    (OUT / "evidence_graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "ingest.cypher").write_text(cypher(nodes, edges), encoding="utf-8")
    counts = {k: len(v) for k, v in nodes.items()}
    print("node counts:", counts)
    print("total claims:", counts["Claim"], "(pack usage section corrected to 12 on 2026-10-17 - in sync)")
    print("edges:", len(edges))
    print("problems:")
    for pr in problems:
        print(" -", pr)
