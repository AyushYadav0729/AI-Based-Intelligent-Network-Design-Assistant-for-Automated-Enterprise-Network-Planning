import React, { useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'

const LAYER_Y = {
  edge: 40,
  core: 160,
  distribution: 300,
  access: 440,
  endpoint: 580,
}

const TYPE_COLORS = {
  internet: 'bg-purple-600 text-white border-purple-700',
  firewall: 'bg-rose-600 text-white border-rose-700',
  router: 'bg-amber-600 text-white border-amber-700',
  core: 'bg-indigo-700 text-white border-indigo-800',
  distribution: 'bg-teal-600 text-white border-teal-700',
  access: 'bg-emerald-600 text-white border-emerald-700',
  server_switch: 'bg-orange-600 text-white border-orange-700',
  wlc: 'bg-sky-600 text-white border-sky-700',
  ap: 'bg-cyan-600 text-white border-cyan-700',
}

export default function TopologyDiagram({ graph, topologyName }) {
  const [selectedNode, setSelectedNode] = useState(null)

  // Layout nodes deterministically by layer and horizontal spacing
  const { nodes, edges } = useMemo(() => {
    if (!graph || !graph.nodes) return { nodes: [], edges: [] }

    // Group nodes by layer
    const byLayer = {}
    graph.nodes.forEach((n) => {
      const layer = n.layer || 'access'
      if (!byLayer[layer]) byLayer[layer] = []
      byLayer[layer].push(n)
    })

    const flowNodes = []
    const layerKeys = ['edge', 'core', 'distribution', 'access', 'endpoint']

    layerKeys.forEach((layer) => {
      const items = byLayer[layer] || []
      const y = LAYER_Y[layer] || 300
      const total = items.length
      const spacing = 190
      const startX = Math.max(80, 500 - (total * spacing) / 2)

      items.forEach((item, idx) => {
        const x = startX + idx * spacing
        flowNodes.push({
          id: item.id,
          position: { x, y },
          data: {
            label: (
              <div className="text-center px-2 py-1">
                <div className="font-bold text-xs truncate max-w-[130px]">{item.label}</div>
                <div className="text-[10px] opacity-80 uppercase tracking-wider">{item.type}</div>
              </div>
            ),
            raw: item,
          },
          className: `shadow-md border-2 rounded-lg font-sans transition-transform hover:scale-105 cursor-pointer ${
            TYPE_COLORS[item.type] || 'bg-gray-700 text-white border-gray-800'
          }`,
          style: { minWidth: '140px' },
        })
      })
    })

    const flowEdges = (graph.edges || []).map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      type: 'smoothstep',
      animated: e.speed === '40G' || e.type === 'fiber',
      style: {
        stroke: e.speed === '40G' ? '#6366f1' : e.speed === '10G' ? '#0284c7' : '#94a3b8',
        strokeWidth: e.speed === '40G' ? 3 : e.speed === '10G' ? 2.5 : 1.5,
      },
      labelStyle: { fontSize: 10, fill: '#475569', fontWeight: 600 },
      markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12 },
    }))

    return { nodes: flowNodes, edges: flowEdges }
  }, [graph])

  return (
    <div className="space-y-4">
      {/* ── Toolbar & Legend ── */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border p-3 rounded-xl shadow-sm text-xs">
        <div className="flex items-center gap-2">
          <span className="font-bold text-gray-700 uppercase tracking-wider">Topology:</span>
          <span className="font-semibold text-brand-700 bg-brand-50 px-2.5 py-1 rounded-md border border-brand-200 uppercase">
            {topologyName?.replace('_', ' ')}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-[11px] text-gray-600">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-purple-600" /> WAN/Internet</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-rose-600" /> Firewall</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-indigo-700" /> Core L3</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-teal-600" /> Distribution</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-600" /> Access</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-orange-600" /> Server ToR</span>
        </div>
      </div>

      {/* ── React Flow Canvas ── */}
      <div className="bg-slate-900 border rounded-xl overflow-hidden h-[540px] relative shadow-inner">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={(_, node) => setSelectedNode(node.data.raw)}
          fitView
          fitViewOptions={{ padding: 0.2 }}
        >
          <Background color="#334155" gap={20} size={1} />
          <Controls className="bg-white text-gray-800 shadow rounded-lg border" />
          <MiniMap
            nodeColor={(n) => {
              const type = n.data?.raw?.type
              return type === 'core' ? '#4f46e5' : type === 'firewall' ? '#e11d48' : '#10b981'
            }}
            className="rounded-lg border border-slate-700"
          />
        </ReactFlow>

        {/* ── Node Detail Popup ── */}
        {selectedNode && (
          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm border shadow-xl rounded-xl p-4 w-72 text-xs space-y-2 z-10 animate-in fade-in duration-150">
            <div className="flex items-center justify-between border-b pb-2">
              <span className="font-bold text-gray-900 text-sm">{selectedNode.label}</span>
              <button
                type="button"
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-gray-700 font-bold"
              >
                ✕
              </button>
            </div>
            <div>
              <span className="text-gray-500 uppercase font-semibold text-[10px]">Role / Type</span>
              <div className="font-medium text-gray-800 capitalize">{selectedNode.type?.replace('_', ' ')}</div>
            </div>
            <div>
              <span className="text-gray-500 uppercase font-semibold text-[10px]">Catalog Hardware Model</span>
              <div className="font-medium text-gray-800">{selectedNode.model || 'Generic Device'}</div>
            </div>
            {selectedNode.floor && (
              <div>
                <span className="text-gray-500 uppercase font-semibold text-[10px]">Location</span>
                <div className="font-medium text-gray-800">{selectedNode.floor}</div>
              </div>
            )}
            <div>
              <span className="text-gray-500 uppercase font-semibold text-[10px]">Hierarchy Layer</span>
              <div className="font-medium text-brand-600 capitalize">{selectedNode.layer} Layer</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

