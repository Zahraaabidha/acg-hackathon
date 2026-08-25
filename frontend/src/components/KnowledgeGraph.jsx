import { useMemo, useState } from "react";
import { formatLabel } from "../lib/format";
import { Card } from "./Card";

const WIDTH = 560;
const HEIGHT = 300;
const DRIVER_X = 110;
const TARGET_X = 450;
const NODE_R_DRIVER = 20;
const NODE_R_TARGET = 26;

// Fixed two-column layout instead of a force simulation - with only 6 nodes
// and a clear "drivers feed targets" structure, a deliberate bipartite layout
// reads far more cleanly than any force-directed jumble.
function computeLayout(nodes, edges) {
  const targetIds = nodes.filter((n) => n.isTarget).map((n) => n.id);
  const driverIds = nodes.filter((n) => !n.isTarget).map((n) => n.id);

  // Order drivers so edge curves cross as little as possible: drivers that
  // only feed the first target go near it, drivers feeding both sit in the
  // middle, mirrored for the second target.
  const driverTargetCount = (id) => edges.filter((e) => e.source === id).length;
  const sortedDrivers = [...driverIds].sort((a, b) => driverTargetCount(a) - driverTargetCount(b));

  const driverSpacing = HEIGHT / (sortedDrivers.length + 1);
  const targetSpacing = HEIGHT / (targetIds.length + 1);

  const positioned = {};
  sortedDrivers.forEach((id, i) => {
    positioned[id] = { x: DRIVER_X, y: driverSpacing * (i + 1) };
  });
  targetIds.forEach((id, i) => {
    positioned[id] = { x: TARGET_X, y: targetSpacing * (i + 1) };
  });

  const positionedNodes = nodes.map((n) => ({ ...n, ...positioned[n.id] }));
  return { nodes: positionedNodes, edges };
}

function curvePath(x1, y1, x2, y2) {
  const midX = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
}

export function KnowledgeGraph({ graph, id }) {
  const { nodes, edges } = useMemo(() => computeLayout(graph.nodes, graph.edges), [graph]);
  const nodeById = useMemo(() => Object.fromEntries(nodes.map((n) => [n.id, n])), [nodes]);
  const [hover, setHover] = useState(null); // { type: "node" | "edge", id/index }

  const isDimmed = (kind, ref, index) => {
    if (!hover) return false;
    if (hover.type === "node") {
      if (kind === "node") return ref.id !== hover.id;
      return ref.source !== hover.id && ref.target !== hover.id;
    }
    if (hover.type === "edge") {
      if (kind === "edge") return index !== hover.index;
      const activeEdge = edges[hover.index];
      return ref.id !== activeEdge.source && ref.id !== activeEdge.target;
    }
    return false;
  };

  const activeEdge = hover?.type === "edge" ? edges[hover.index] : null;

  return (
    <Card
      id={id}
      eyebrow="Feature Justification"
      title="Causal driver graph"
      subtitle="Drivers on the left, price targets on the right. Curve thickness scales with correlation strength; dashed = qualitative only (not a model feature). Hover a node or edge for detail."
    >
      <div className="relative mx-auto" style={{ maxWidth: WIDTH }}>
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full select-none">
          {edges.map((edge, i) => {
            const s = nodeById[edge.source];
            const t = nodeById[edge.target];
            const dimmed = isDimmed("edge", edge, i);
            const x1 = s.x + NODE_R_DRIVER;
            const x2 = t.x - NODE_R_TARGET - 8;

            return (
              <g key={i}>
                <path
                  d={curvePath(x1, s.y, x2, t.y)}
                  fill="none"
                  stroke={edge.modelInput ? "var(--color-ink-secondary)" : "var(--color-hairline)"}
                  strokeWidth={1.2 + Math.abs(edge.correlation) * 3}
                  strokeDasharray={edge.modelInput ? undefined : "4 4"}
                  opacity={dimmed ? 0.15 : 0.8}
                  className="cursor-pointer transition-opacity"
                  onMouseEnter={() => setHover({ type: "edge", index: i })}
                  onMouseLeave={() => setHover(null)}
                />
                <polygon
                  points={`${x2},${t.y - 4} ${x2},${t.y + 4} ${x2 + 7},${t.y}`}
                  fill={edge.modelInput ? "var(--color-ink-secondary)" : "var(--color-hairline)"}
                  opacity={dimmed ? 0.15 : 0.85}
                  className="pointer-events-none transition-opacity"
                />
              </g>
            );
          })}

          {nodes.map((n) => {
            const dimmed = isDimmed("node", n);
            const r = n.isTarget ? NODE_R_TARGET : NODE_R_DRIVER;
            const labelSide = n.isTarget ? "end" : "start";
            const labelX = n.isTarget ? n.x - r - 10 : n.x + r + 10;

            return (
              <g
                key={n.id}
                className="cursor-pointer transition-opacity"
                opacity={dimmed ? 0.3 : 1}
                onMouseEnter={() => setHover({ type: "node", id: n.id })}
                onMouseLeave={() => setHover(null)}
              >
                <circle cx={n.x} cy={n.y} r={r} fill={n.color} stroke="var(--color-surface)" strokeWidth={2.5} />
                <text
                  x={labelX}
                  y={n.y}
                  dy="0.35em"
                  textAnchor={labelSide}
                  fontSize={n.isTarget ? 12 : 11}
                  fontWeight={n.isTarget ? 700 : 500}
                  fill="var(--color-ink-primary)"
                  className="font-display capitalize"
                >
                  {formatLabel(n.id)}
                </text>
              </g>
            );
          })}
        </svg>

        {activeEdge && (
          <div className="pointer-events-none absolute bottom-2 left-2 max-w-xs rounded-[4px] border border-[var(--color-hairline)] bg-[var(--color-surface-raised)] p-3 text-xs shadow-md">
            <p className="font-display font-semibold capitalize text-[var(--color-ink-primary)]">
              {formatLabel(activeEdge.source)} → {formatLabel(activeEdge.target)}
            </p>
            <p className="mt-1 leading-relaxed text-[var(--color-ink-secondary)]">{activeEdge.relationship}</p>
            <p className="mt-1.5 tabular-nums text-[var(--color-ink-primary)]">
              correlation {activeEdge.correlation.toFixed(2)} ·{" "}
              {activeEdge.lagMonths ? `${activeEdge.lagMonths}mo lag` : "same-month"}
            </p>
            <p className="mt-1 text-[var(--color-ink-muted)]">
              {activeEdge.modelInput ? "Used as model feature" : "Qualitative only - not a model feature"}
            </p>
          </div>
        )}

        <div className="mt-1 flex items-center justify-between text-[11px] text-[var(--color-ink-muted)]">
          <span>← Drivers</span>
          <span>Price targets →</span>
        </div>
      </div>
    </Card>
  );
}
