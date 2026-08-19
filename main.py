"""
End-to-end demo: build the causal knowledge graph, print upstream drivers and
feature-selection justification for each price target, and export the
interactive HTML visualization.

Run with:
    python main.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from knowledge_graph import build_graph, get_model_input_features, get_upstream_drivers
from visualize_graph import build_visualization

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "price_driver_graph.html")
TARGETS = ["aluminium_price", "pvc_resin_price"]
MIN_CORRELATION = 0.65


def print_justification(graph, target: str) -> None:
    drivers = get_upstream_drivers(graph, target)
    print(f"\nUpstream causal drivers for '{target}': {', '.join(sorted(drivers))}")

    features = get_model_input_features(graph, target, min_correlation=MIN_CORRELATION)
    if not features:
        print(f"{target}: no upstream driver clears correlation > {MIN_CORRELATION} for model input.")
        return

    labels = [f"{name} ({lag}mo lag)" if lag else name for name, _corr, lag in features]
    verb = "sit" if len(labels) > 1 else "sits"
    subject = "both" if len(labels) == 2 else ("all" if len(labels) > 2 else "it")
    print(
        f"{target} features selected: {', '.join(labels)} - {subject} {verb} on a causal "
        f"path with correlation >{MIN_CORRELATION}"
    )


def main():
    graph = build_graph()

    for target in TARGETS:
        print_justification(graph, target)

    build_visualization(graph, OUTPUT_PATH)
    print(f"\nInteractive graph written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
