import React, { useEffect, useState } from 'react'
import { getProjects, deleteProject, compareProjects } from '../api/client'

export default function ProjectsPage() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedIds, setSelectedIds] = useState([])
  const [compareData, setCompareData] = useState(null)
  const [isComparing, setIsComparing] = useState(false)

  const fetchProjects = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getProjects()
      setProjects(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete project "${name}"?`)) return
    try {
      await deleteProject(id)
      setProjects((prev) => prev.filter((p) => p.id !== id))
      setSelectedIds((prev) => prev.filter((i) => i !== id))
    } catch (err) {
      alert('Delete failed: ' + (err.response?.data?.detail || err.message))
    }
  }

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const handleCompare = async () => {
    if (selectedIds.length < 2) return
    setIsComparing(true)
    try {
      const res = await compareProjects(selectedIds)
      setCompareData(res.data)
    } catch (err) {
      alert('Comparison failed: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsComparing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* ── Top Header Bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border p-4 rounded-xl shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Saved Network Design Projects</h1>
          <p className="text-xs text-gray-500">
            Archived enterprise network designs saved in SQLite database
          </p>
        </div>

        <div className="flex items-center gap-3">
          {selectedIds.length >= 2 && (
            <button
              type="button"
              onClick={handleCompare}
              disabled={isComparing}
              className="bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs px-4 py-2 rounded-lg shadow-sm transition flex items-center gap-1.5"
            >
              📊 Compare Selected ({selectedIds.length})
            </button>
          )}
          <button
            type="button"
            onClick={fetchProjects}
            className="border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold text-xs px-3.5 py-2 rounded-lg transition"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-xl">
          ⚠ {error}
        </div>
      )}

      {/* ── Projects List ── */}
      {loading ? (
        <div className="text-center py-12 text-sm text-gray-400">Loading saved projects...</div>
      ) : projects.length === 0 ? (
        <div className="bg-white border rounded-xl p-12 text-center space-y-3">
          <div className="text-4xl">📂</div>
          <h3 className="text-base font-bold text-gray-700">No Saved Projects Yet</h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto">
            Design a new network in the wizard and click "Save Project" to archive and compare multiple enterprise architectures here.
          </p>
        </div>
      ) : (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b text-gray-600">
                <th className="py-3 px-4 w-10 text-center">Select</th>
                <th className="py-3 px-4 font-semibold">Project Name</th>
                <th className="py-3 px-4 font-semibold">Org Type</th>
                <th className="py-3 px-4 font-semibold">Topology</th>
                <th className="py-3 px-4 font-semibold">Balanced Cost</th>
                <th className="py-3 px-4 font-semibold">Saved Date</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {projects.map((p) => {
                const isSelected = selectedIds.includes(p.id)
                return (
                  <tr key={p.id} className={`hover:bg-gray-50/60 ${isSelected ? 'bg-brand-50/30' : ''}`}>
                    <td className="py-3 px-4 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(p.id)}
                        className="w-4 h-4 text-brand-600 rounded"
                      />
                    </td>
                    <td className="py-3 px-4 font-bold text-gray-900">{p.name}</td>
                    <td className="py-3 px-4">
                      <span className="capitalize px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-700">
                        {p.org_type?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-brand-700 capitalize">
                        {p.topology ? p.topology.replace('_', ' ') : '—'}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-gray-800">
                      {p.balanced_cost ? `$${p.balanced_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="py-3 px-4 text-gray-500">
                      {new Date(p.created_at).toLocaleDateString()} {new Date(p.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => handleDelete(p.id, p.name)}
                        className="text-rose-600 hover:text-rose-800 font-bold text-xs transition"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Compare Modal ── */}
      {compareData && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Side-by-Side Project Comparison</h2>
                <p className="text-xs text-gray-500">
                  Comparing {compareData.projects?.length} saved architectures
                </p>
              </div>
              <button
                type="button"
                onClick={() => setCompareData(null)}
                className="text-gray-400 hover:text-gray-700 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            {/* Comparison Table */}
            <div className="border rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-gray-100 border-b text-gray-700">
                    <th className="py-3 px-4 font-bold w-1/3">Metric</th>
                    {compareData.projects?.map((proj) => (
                      <th key={proj.id} className="py-3 px-4 font-bold text-center">
                        <div className="font-bold text-sm text-brand-800">{proj.name}</div>
                        <div className="text-[10px] text-gray-500 font-normal capitalize">
                          {proj.org_type?.replace('_', ' ')}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {compareData.comparison_metrics?.map((m, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/60">
                      <td className="py-3 px-4 font-semibold text-gray-800">{m.label}</td>
                      {compareData.projects?.map((proj) => (
                        <td key={proj.id} className="py-3 px-4 text-center font-bold text-gray-900">
                          {m.values?.[proj.name] ?? '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setCompareData(null)}
                className="bg-gray-800 hover:bg-gray-900 text-white font-bold text-xs px-5 py-2.5 rounded-lg transition"
              >
                Close Comparison
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
