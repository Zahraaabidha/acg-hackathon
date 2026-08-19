"""
Render the causal knowledge graph as an interactive, physics-enabled HTML
visualization using pyvis. Edge thickness and tooltips reflect the actual
correlation strength from correlation_analysis.py, not placeholder values.
"""

import os

from pyvis.network import Network

from knowledge_graph import CATEGORY_COLORS

# Target nodes are drawn larger so they visually stand out as "outcome" nodes.
TARGET_NODES = {"pvc_resin_price", "aluminium_price"}
DEFAULT_NODE_SIZE = 22
TARGET_NODE_SIZE = 38

# Targets get a fixed color per chain instead of the generic
# CATEGORY_COLORS["target"] placeholder.
TARGET_COLORS = {
    "pvc_resin_price": "#c0392b",  # deep coral (PVC chain outcome)
    "aluminium_price": "#2c5aa0",  # deep blue (aluminium chain outcome)
}

# Edge width scales with |correlation| so the strongest drivers visually pop.
MIN_EDGE_WIDTH = 1
MAX_EDGE_WIDTH = 10


def _node_color(graph, node_name: str) -> str:
    node_data = graph.nodes[node_name]
    if node_name in TARGET_NODES:
        return TARGET_COLORS[node_name]
    return CATEGORY_COLORS.get(node_data["category"], "#9e9e9e")


def _node_tooltip(node_name: str, node_data: dict) -> str:
    return f"{node_name}\ncategory: {node_data['category']}"


def _edge_width(correlation: float) -> float:
    return MIN_EDGE_WIDTH + abs(correlation) * (MAX_EDGE_WIDTH - MIN_EDGE_WIDTH)


def _edge_tooltip(edge_data: dict) -> str:
    lag = edge_data["lag_months"]
    lag_text = f"{lag}-month lag" if lag else "same-month"
    input_text = "used as model feature" if edge_data["model_input"] else "qualitative only - not a model feature"

    return (
        f"{edge_data['relationship']}\n"
        f"correlation: {edge_data['correlation']:+.2f} ({lag_text})\n"
        f"{input_text}"
    )


def build_visualization(graph, output_path: str) -> None:
    """Export graph to an interactive, draggable HTML file at output_path."""
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#ffffff",
        font_color="#222222",
    )
    net.barnes_hut()  # physics engine, makes the graph draggable/interactive

    for node_name, node_data in graph.nodes(data=True):
        net.add_node(
            node_name,
            label=node_name,
            title=_node_tooltip(node_name, node_data),
            color=_node_color(graph, node_name),
            size=TARGET_NODE_SIZE if node_name in TARGET_NODES else DEFAULT_NODE_SIZE,
        )

    for source, target, edge_data in graph.edges(data=True):
        net.add_edge(
            source,
            target,
            title=_edge_tooltip(edge_data),
            value=_edge_width(edge_data["correlation"]),
            arrows="to",
            # dashed edges mark qualitative-only links (freight_index) so the
            # "not a model feature" distinction is visible at a glance
            dashes=not edge_data["model_input"],
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    net.write_html(output_path, notebook=False)
