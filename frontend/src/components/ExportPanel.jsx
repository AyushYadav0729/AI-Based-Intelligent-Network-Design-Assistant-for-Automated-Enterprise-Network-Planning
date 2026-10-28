/**
 * ExportPanel.jsx — Step 4 Export Panel.
 * Spec Section 13 (Frontend wizard, Step 4: Export).
 *
 * Provides:
 *  - Download PDF report (with optional diagram PNG from React Flow canvas)
 *  - Download CLI configs as ZIP
 *  - Download topology diagram PNG (via html-to-image on the React Flow canvas)
 *  - Download topology diagram PDF
 *  - Save project to database
 */
import React, { useState, useRef } from 'react'
import { exportPdf, exportConfig, exportDiagramPng } from '../api/client'

// ── Utility: trigger a file download from a Blob ────────────────────────────
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ── Utility: capture the React Flow canvas as a PNG Base64 ─────────────────
async function captureTopologyPng(diagramContainerId) {
  try {
    const { toPng } = await import('html-to-image')
    const el = document.getElementById(diagramContainerId)
    if (!el) return null
    const dataUrl = await toPng(el, { quality: 0.95, backgroundColor: '#f8fafc' })
    return dataUrl.split(',')[1] // strip "data:image/png;base64,"
  } catch {
    return null
  }
}

// ── Status badge ────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    idle:     { bg: 'bg-slate-100',   text: 'text-slate-600',  label: '' },
    loading:  { bg: 'bg-indigo-100',  text: 'text-indigo-700', label: '⏳ Generating…' },
    success:  { bg: 'bg-emerald-100', text: 'text-emerald-700', label: '✓ Downloaded!' },
    error:    { bg: 'bg-rose-100',    text: 'text-rose-700',   label: '✗ Error' },
  }
  const { bg, text, label } = map[status] || map.idle
  if (!label) return null
  return (
    <span className={`ml-2 text-xs font-semibold px-2 py-0.5 rounded-full ${bg} ${text}`}>
      {label}
    </span>
  )
}

// ── Export card ──────────────────────────────────────────────────────────────
function ExportCard({ icon, title, description, buttonLabel, onExport, status, accent = 'indigo', disabled = false }) {
  const colors = {
    indigo: {
      btn: 'bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300',
      icon: 'bg-indigo-100 text-indigo-600',
      border: 'border-indigo-200 hover:border-indigo-400',
    },
    violet: {
      btn: 'bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300',
      icon: 'bg-violet-100 text-violet-600',
      border: 'border-violet-200 hover:border-violet-400',
    },
    emerald: {
      btn: 'bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300',
      icon: 'bg-emerald-100 text-emerald-600',
      border: 'border-emerald-200 hover:border-emerald-400',
    },
    amber: {
      btn: 'bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300',
      icon: 'bg-amber-100 text-amber-600',
      border: 'border-amber-200 hover:border-amber-400',
    },
  }
  const c = colors[accent] || colors.indigo

  return (
    <div className={`bg-white rounded-2xl border-2 ${c.border} p-6 flex flex-col gap-4 shadow-sm transition-all hover:shadow-md`}>
      <div className="flex items-start gap-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 ${c.icon}`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-bold text-slate-900 text-sm">{title}</div>
          <div className="text-xs text-slate-500 mt-1 leading-relaxed">{description}</div>
        </div>
      </div>
      <button
        type="button"
        onClick={onExport}
        disabled={disabled || status === 'loading'}
        className={`w-full py-2.5 px-4 rounded-xl text-white text-sm font-bold transition flex items-center justify-center gap-2 ${c.btn}`}
      >
        {status === 'loading' ? (
          <>
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Generating…
          </>
        ) : buttonLabel}
        <StatusBadge status={status === 'loading' ? 'idle' : status} />
      </button>
    </div>
  )
}

// ── Main ExportPanel component ──────────────────────────────────────────────
export default function ExportPanel({
  design,
  requirements,
  designResponse,
  activeVariant,
  onSaveProject,
  savedSuccess,
  diagramSnapshot,
}) {
  const [pdfStatus, setPdfStatus]       = useState('idle')
  const [configStatus, setConfigStatus] = useState('idle')
  const [pngStatus, setPngStatus]       = useState('idle')
  const [saveStatus, setSaveStatus]     = useState('idle')

  const orgName = requirements?.org_name || 'network_design'
  const variant = activeVariant || design?.variant || 'balanced'

  // ── PDF Export ─────────────────────────────────────────────────────────
  const handlePdfExport = async () => {
    setPdfStatus('loading')
    try {
      // 1. Prioritize pre-captured high-res canvas snapshot
      let diagramPng = null
      if (diagramSnapshot && diagramSnapshot.includes(',')) {
        diagramPng = diagramSnapshot.split(',')[1]
      } else {
        diagramPng = await captureTopologyPng('cisco-topology-canvas')
      }

      const payload = {
        design,
        requirements,
        comparison: designResponse?.comparison || null,
        comparison_summary: designResponse?.comparison_summary || '',
        diagram_png_b64: diagramPng,
      }

      const res = await exportPdf(payload)
      const blob = new Blob([res.data], { type: 'application/pdf' })
      downloadBlob(blob, `${orgName.replace(/\s+/g, '_')}_${variant}_report.pdf`)
      setPdfStatus('success')
      setTimeout(() => setPdfStatus('idle'), 3000)
    } catch (err) {
      console.error('PDF export error:', err)
      setPdfStatus('error')
      setTimeout(() => setPdfStatus('idle'), 4000)
    }
  }

  // ── CLI Config ZIP Export ───────────────────────────────────────────────
  const handleConfigExport = async () => {
    setConfigStatus('loading')
    try {
      const res = await exportConfig(design)
      const blob = new Blob([res.data], { type: 'application/zip' })
      downloadBlob(blob, `cli_configs_${variant}.zip`)
      setConfigStatus('success')
      setTimeout(() => setConfigStatus('idle'), 3000)
    } catch (err) {
      console.error('Config export error:', err)
      setConfigStatus('error')
      setTimeout(() => setConfigStatus('idle'), 4000)
    }
  }

  // ── Topology PNG export (Prioritizes snapshot, with un-hide & server fallback) ─
  const handlePngExport = async () => {
    setPngStatus('loading')
    try {
      // Strategy 1: Use pristine snapshot if available
      if (diagramSnapshot && diagramSnapshot.length > 5000) {
        const a = document.createElement('a')
        a.href = diagramSnapshot
        a.download = `cisco-topology-${variant}.png`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        setPngStatus('success')
        setTimeout(() => setPngStatus('idle'), 3000)
        return
      }

      // Strategy 2: Live capture of the canvas element (un-hiding if necessary)
      const canvasEl = document.getElementById('cisco-topology-canvas')
      const wrapper = document.getElementById('topology-diagram-container')
      let wasHidden = false

      if (wrapper && wrapper.style.display === 'none') {
        wasHidden = true
        wrapper.style.display = 'block'
        wrapper.style.position = 'fixed'
        wrapper.style.left = '0'
        wrapper.style.top = '0'
        wrapper.style.zIndex = '-999'
        wrapper.style.opacity = '1'
        await new Promise((r) => setTimeout(r, 80))
      }

      const targetEl = document.getElementById('cisco-topology-canvas') || wrapper
      if (targetEl) {
        const { toPng } = await import('html-to-image')
        const dataUrl = await toPng(targetEl, {
          quality: 0.95,
          backgroundColor: '#f8fafc',
        })

        if (wasHidden && wrapper) {
          wrapper.style.display = 'none'
          wrapper.style.position = ''
          wrapper.style.left = ''
          wrapper.style.top = ''
          wrapper.style.zIndex = ''
          wrapper.style.opacity = ''
        }

        // Only accept if image contains substantial pixel data
        if (dataUrl && dataUrl.length > 5000) {
          const a = document.createElement('a')
          a.href = dataUrl
          a.download = `cisco-topology-${variant}.png`
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          setPngStatus('success')
          setTimeout(() => setPngStatus('idle'), 3000)
          return
        }
      }

      if (wasHidden && wrapper) {
        wrapper.style.display = 'none'
        wrapper.style.position = ''
        wrapper.style.left = ''
        wrapper.style.top = ''
        wrapper.style.zIndex = ''
        wrapper.style.opacity = ''
      }

      // Strategy 3: Server-side generator fallback
      const res = await exportDiagramPng(design)
      const blob = new Blob([res.data], { type: 'image/png' })
      downloadBlob(blob, `cisco-topology-${variant}.png`)
      setPngStatus('success')
      setTimeout(() => setPngStatus('idle'), 3000)
    } catch (err) {
      console.warn('Browser capture failed, using server fallback:', err)
      try {
        const res = await exportDiagramPng(design)
        const blob = new Blob([res.data], { type: 'image/png' })
        downloadBlob(blob, `cisco-topology-${variant}.png`)
        setPngStatus('success')
        setTimeout(() => setPngStatus('idle'), 3000)
      } catch (fallbackErr) {
        console.error('All PNG export strategies failed:', fallbackErr)
        setPngStatus('error')
        setTimeout(() => setPngStatus('idle'), 4000)
      }
    }
  }

  // ── Save Project ─────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaveStatus('loading')
    try {
      await onSaveProject()
      setSaveStatus('success')
      setTimeout(() => setSaveStatus('idle'), 3000)
    } catch {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 4000)
    }
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-900 rounded-2xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-white/10 backdrop-blur rounded-xl flex items-center justify-center text-xl">
            📦
          </div>
          <div>
            <div className="font-bold text-lg">Export & Save</div>
            <div className="text-slate-300 text-sm">
              Download your design artifacts or save to the project archive
            </div>
          </div>
        </div>

        {/* Design summary strip */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Organisation', value: requirements?.org_name || '—' },
            { label: 'Topology', value: design?.topology?.replace('_', ' ') || '—' },
            { label: 'Variant', value: variant.replace('_', ' ') },
            { label: 'Total Cost', value: design?.cost?.total_cost
                ? `$${design.cost.total_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                : '—' },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white/10 backdrop-blur rounded-xl p-3">
              <div className="text-slate-300 text-xs">{label}</div>
              <div className="font-bold text-sm capitalize mt-0.5 truncate">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Notice ── */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-800 flex items-start gap-2">
        <span className="text-amber-500 text-sm mt-0.5">⚠</span>
        <span>
          All exported configurations are <strong>samples</strong> generated from a deterministic model.
          Review with a qualified network engineer and test in a lab environment before production deployment.
        </span>
      </div>

      {/* ── Export cards grid ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ExportCard
          icon="📄"
          accent="indigo"
          title="Full PDF Design Report"
          description={
            'Multi-section PDF including requirements summary, topology diagram, VLAN plan, ' +
            'IP addressing, device BOM & costs, security ACLs, validation results, and decision log.'
          }
          buttonLabel="⬇ Download PDF Report"
          onExport={handlePdfExport}
          status={pdfStatus}
        />

        <ExportCard
          icon="🖥"
          accent="violet"
          title="Cisco IOS CLI Configs (ZIP)"
          description={
            'Per-device configuration files for core switch, access switches, and firewall/edge router. ' +
            'Includes VLANs, SVIs, OSPF/static routing, ACLs, port security, DHCP snooping, and SSH hardening.'
          }
          buttonLabel="⬇ Download CLI Configs (.zip)"
          onExport={handleConfigExport}
          status={configStatus}
        />

        <ExportCard
          icon="🖼"
          accent="amber"
          title="Topology Diagram PNG"
          description={
            'Exports the high-resolution Cisco Packet Tracer topology diagram as a clean PNG image, ' +
            'capturing all switches, routers, firewalls, and interface port labels.'
          }
          buttonLabel="⬇ Download Diagram PNG"
          onExport={handlePngExport}
          status={pngStatus}
        />

        <ExportCard
          icon="💾"
          accent="emerald"
          title="Save to Project Archive"
          description={
            'Saves the full design (all 3 variants + comparison) to the local SQLite database. ' +
            'Accessible from the My Projects page for future review and comparison.'
          }
          buttonLabel="💾 Save Project to Database"
          onExport={handleSave}
          status={saveStatus}
        />
      </div>

      {/* ── Topology Diagram Snapshot Preview ── */}
      {diagramSnapshot && (
        <div className="bg-white border rounded-xl p-4 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
              <span>🖼</span> Cisco Packet Tracer Topology Preview
            </span>
            <span className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-bold">
              ✓ Snapshot Ready
            </span>
          </div>
          <div className="rounded-lg overflow-hidden border border-slate-200 max-h-56 flex items-center justify-center bg-slate-50 p-2">
            <img
              src={diagramSnapshot}
              alt="Topology Diagram Preview"
              className="w-full h-auto object-contain max-h-52 rounded"
            />
          </div>
        </div>
      )}

      {/* ── CLI Config preview ── */}
      <div className="bg-slate-900 rounded-2xl p-5">
        <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">
          CLI Config File List Preview
        </div>
        <div className="font-mono text-xs text-slate-300 space-y-1">
          {getCLIPreviewFiles(design).map(fname => (
            <div key={fname} className="flex items-center gap-2">
              <span className="text-indigo-400">📄</span>
              <span>{fname}</span>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <span className="text-emerald-400">📋</span>
            <span>README.txt</span>
          </div>
        </div>
      </div>

      {/* ── What's included info ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        {[
          {
            title: 'PDF Report Contains',
            items: [
              'Cover page & organisation summary',
              'VLAN plan & IP addressing table',
              'Topology diagram (PNG embedded)',
              'Devices BOM & cost breakdown',
              'Bandwidth & oversubscription',
              'ACL matrix heatmap',
              'Validation results (all 21 rules)',
              'Variant comparison table',
              'Decision log & explanations',
              'Assumptions & limitations',
            ],
            icon: '📄',
            color: 'indigo',
          },
          {
            title: 'CLI ZIP Contains',
            items: [
              'CORE-SW-1.txt (L3 core config)',
              'CORE-SW-2.txt (if redundant pair)',
              'ACC-SW-F1-1.txt … (per floor)',
              'FW-EDGE-1.txt (firewall/edge)',
              'FW-EDGE-2.txt (if HA pair)',
              'README.txt (usage instructions)',
              'VLANs, SVIs, OSPF/static routing',
              'ACLs from security matrix',
              '802.1X, DHCP snooping, DAI',
              'SSH hardening, port security',
            ],
            icon: '🖥',
            color: 'violet',
          },
          {
            title: 'Important Notes',
            items: [
              'All configs are sample templates',
              'Interface numbers are illustrative',
              'Replace [CHANGE_ME] placeholders',
              'Verify PoE power budgets',
              'Test in Packet Tracer / lab first',
              'Cisco IOS / IOS-XE syntax only',
              'Not NX-OS compatible as-is',
              'IPv4 only (no IPv6 config)',
              'Review with network engineer',
              'Not for direct production use',
            ],
            icon: '⚠',
            color: 'amber',
          },
        ].map(({ title, items, icon, color }) => {
          const borderMap = { indigo: 'border-indigo-200', violet: 'border-violet-200', amber: 'border-amber-200' }
          const headerMap = { indigo: 'bg-indigo-50 text-indigo-700', violet: 'bg-violet-50 text-violet-700', amber: 'bg-amber-50 text-amber-700' }
          return (
            <div key={title} className={`bg-white rounded-xl border ${borderMap[color]} overflow-hidden`}>
              <div className={`px-4 py-2.5 font-bold text-xs ${headerMap[color]}`}>
                {icon} {title}
              </div>
              <ul className="px-4 py-3 space-y-1.5 text-slate-600">
                {items.map(item => (
                  <li key={item} className="flex items-start gap-1.5">
                    <span className="text-slate-300 mt-0.5">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Helper: estimate file list from design ──────────────────────────────────
function getCLIPreviewFiles(design) {
  if (!design) return ['CORE-SW-1.txt', 'ACC-SW-F1-1.txt', 'FW-EDGE-1.txt']
  const files = []
  const coreDevices = design.devices?.filter(d => d.role === 'core' || d.role === 'distribution') || []
  const coreCount = Math.max(1, coreDevices.reduce((s, d) => s + d.quantity, 0))
  for (let i = 1; i <= Math.min(coreCount, 2); i++) files.push(`CORE-SW-${i}.txt`)

  const accessDevices = design.devices?.filter(d => d.role === 'access') || []
  const accessCount = Math.min(4, Math.max(1, accessDevices.reduce((s, d) => s + d.quantity, 0)))
  for (let i = 1; i <= accessCount; i++) {
    const floor = Math.ceil(i / 2)
    const idx = ((i - 1) % 2) + 1
    files.push(`ACC-SW-F${floor}-${idx}.txt`)
  }

  const fwDevices = design.devices?.filter(d => d.role === 'firewall') || []
  const fwCount = Math.max(1, Math.min(2, fwDevices.reduce((s, d) => s + d.quantity, 0)))
  for (let i = 1; i <= fwCount; i++) files.push(`FW-EDGE-${i}.txt`)

  return files
}
