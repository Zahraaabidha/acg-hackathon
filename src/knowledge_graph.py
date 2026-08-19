"""
Causal knowledge graph for raw material (aluminium, PVC resin) price drivers.

The graph is directed: an edge A -> B means "A causally influences B". Edge
weights are the actual Pearson correlations from correlation_analysis.py
(step 2), not placeholders - this graph is the feature-selection justification
for the forecasting model, so the numbers on it have to be real.

Node names match the columns in data/rm_price_data.csv so the graph lines up
directly with the modeling pipeline (feature_engineering.py, forecast_model.py).
"""

import networkx as nx

# Category -> base color, used by visualize_graph.py
CATEGORY_COLORS = {
    "feedstock": "#e8734a",  # coral - crude_oil_price (PVC's dominant driver, also feeds aluminium)
    "currency": "#4a78e8",   # blue - usd_inr_rate (aluminium-side driver)
    "logistics": "#9e9e9e",  # gray - freight_index (shared, qualitative-only)
    "energy": "#1f9e89",     # teal - energy_price_index (aluminium-side driver)
    "target": None,          # resolved per node in visualize_graph.py
}


def _add_node(graph: nx.DiGraph, name: str, category: str) -> None:
    graph.add_node(name, name=name, category=category)


def _add_edge(
    graph: nx.DiGraph,
    source: str,
    target: str,
    relationship: str,
    correlation: float,
    lag_months: int,
    model_input: bool,
) -> None:
    """
    correlation: Pearson correlation from correlation_analysis.py (step 2).
    lag_months: the lag (in months) that correlation was measured at.
    model_input: whether this driver is actually used as a Ridge/SARIMAX
        feature (see feature_engineering.py) or is kept only as qualitative
        context in the graph (e.g. freight_index, which was dropped from the
        feature set for having the weakest correlation with both targets).
    """
    graph.add_edge(
        source,
        target,
        relationship=relationship,
        correlation=correlation,
        lag_months=lag_months,
        model_input=model_input,
    )


def build_graph() -> nx.DiGraph:
    """Build the causal knowledge graph for PVC resin and aluminium prices."""
    graph = nx.DiGraph()

    # --- Nodes -----------------------------------------------------------
    _add_node(graph, "crude_oil_price", "feedstock")
    _add_node(graph, "usd_inr_rate", "currency")
    _add_node(graph, "freight_index", "logistics")
    _add_node(graph, "energy_price_index", "energy")
    _add_node(graph, "pvc_resin_price", "target")
    _add_node(graph, "aluminium_price", "target")

    # --- PVC resin chain ---------------------------------------------------
    _add_edge(
        graph, "crude_oil_price", "pvc_resin_price",
        relationship="1-month lagged crude oil price feeds naphtha cost, PVC resin's primary feedstock",
        correlation=0.79, lag_months=1, model_input=True,
    )
    _add_edge(
        graph, "freight_index", "pvc_resin_price",
        relationship="higher freight rates raise the landed cost of imported PVC resin",
        correlation=0.33, lag_months=0, model_input=False,
    )

    # --- Aluminium chain -----------------------------------------------------
    _add_edge(
        graph, "crude_oil_price", "aluminium_price",
        relationship="same-month crude oil price correlates with aluminium price via energy/production cost",
        correlation=0.70, lag_months=0, model_input=True,
    )
    _add_edge(
        graph, "usd_inr_rate", "aluminium_price",
        relationship="a weaker rupee raises the cost of dollar-denominated aluminium/alumina imports; "
                     "stays strongly correlated through a 6-month lag",
        correlation=0.66, lag_months=6, model_input=True,
    )
    _add_edge(
        graph, "freight_index", "aluminium_price",
        relationship="higher freight rates raise the landed cost of imported aluminium",
        correlation=0.18, lag_months=0, model_input=False,
    )
    _add_edge(
        graph, "energy_price_index", "aluminium_price",
        relationship="aluminium smelting is energy-intensive; US electric power PPI (FRED PCU221122221122) "
                     "correlates with aluminium price same-month",
        correlation=0.674, lag_months=0, model_input=True,
    )

    return graph


def get_upstream_drivers(graph: nx.DiGraph, target_node: str) -> list:
    """
    Return every node with a directed causal path into target_node - the
    full causal picture, including qualitative-only drivers like
    freight_index that aren't used as model features.
    """
    if target_node not in graph:
        raise ValueError(f"Unknown node: {target_node!r}")
    return list(nx.ancestors(graph, target_node))


def get_model_input_features(
    graph: nx.DiGraph, target_node: str, min_correlation: float = 0.65
) -> list:
    """
    Return the direct upstream drivers actually used as forecasting-model
    features for target_node: edges flagged model_input=True whose
    correlation clears min_correlation. This is the subset of
    get_upstream_drivers() that justifies feature selection - a driver can be
    causally real (freight_index) without being strong/quantitative enough
    to include as a regression feature.

    Returns a list of (node_name, correlation, lag_months) tuples, sorted by
    correlation descending.
    """
    if target_node not in graph:
        raise ValueError(f"Unknown node: {target_node!r}")

    features = []
    for source in graph.predecessors(target_node):
        edge = graph.edges[source, target_node]
        if edge["model_input"] and edge["correlation"] >= min_correlation:
            features.append((source, edge["correlation"], edge["lag_months"]))

    return sorted(features, key=lambda item: item[1], reverse=True)
