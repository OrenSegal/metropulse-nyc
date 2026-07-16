# Run from repo root: python scripts/render_asset_graph.py
# Requires: pip install graphviz + the graphviz system package (brew install graphviz)
import graphviz

# Real dependency structure, extracted from the @asset() signatures in
# dagster_pipeline/assets/*.py — each asset's function parameters are its
# Dagster inputs, so the graph below is a direct transcription, not a
# hand-drawn approximation.
GROUP_COLORS = {
    "ingestion": "#4C72B0",
    "enrichment": "#55A868",
    "ml": "#C44E52",
    "ai": "#8172B2",
}

NODES = {
    "fetch_mta_data": ("ingestion", "dagster_pipeline/assets/ingestion.py"),
    "fetch_poi_features": ("enrichment", "dagster_pipeline/assets/features.py"),
    "train_cluster_model": ("ml", "dagster_pipeline/assets/modeling.py"),
    "generate_personas": ("ai", "dagster_pipeline/assets/personas.py"),
}

EDGES = [
    ("fetch_mta_data", "fetch_poi_features"),
    ("fetch_mta_data", "train_cluster_model"),
    ("fetch_poi_features", "train_cluster_model"),
    ("train_cluster_model", "generate_personas"),
]

g = graphviz.Digraph("asset_graph", format="png")
g.attr(rankdir="LR", bgcolor="#1e1e1e", fontname="Helvetica", pad="0.4")
g.attr("node", shape="box", style="filled,rounded", fontname="Helvetica",
       fontcolor="white", color="#444444", penwidth="1.5")
g.attr("edge", color="#888888", penwidth="1.2", arrowsize="0.8")

for name, (group, src) in NODES.items():
    label = f"{name}\\n{{{group}}}\\n{src}"
    g.node(name, label=label, fillcolor=GROUP_COLORS[group])

for a, b in EDGES:
    g.edge(a, b)

g.render("docs/asset_graph", cleanup=True)
print("wrote docs/asset_graph.png")
