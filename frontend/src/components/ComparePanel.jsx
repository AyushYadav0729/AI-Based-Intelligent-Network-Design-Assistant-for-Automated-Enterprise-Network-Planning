import React from 'react'

export default function ComparePanel({ comparison, summary, onSelectVariant, activeVariant }) {
  const rows = comparison || []

  return (
    <div className="space-y-6">
      {/* ── Executive Comparison Summary ── */}
      {summary && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 shadow-sm text-xs text-blue-950 space-y-1.5">
          <span className="font-bold uppercase tracking-wider text-blue-800 text-[11px]">
            Executive Design Comparison
          </span>
          <p className="leading-relaxed text-sm font-medium">{summary}</p>
        </div>
      )}

      {/* ── Side-by-Side Table ── */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse font-sans">
            <thead>
              <tr className="bg-gray-100/70 border-b text-gray-700">
                <th className="py-3 px-4 font-bold text-sm w-1/4">Architecture Feature</th>
                <th className="py-3 px-4 font-bold text-center w-1/4 text-emerald-800 bg-emerald-50/50">
                  <div className="text-sm">Budget Tier</div>
                  <div className="text-[10px] font-normal text-gray-500">Value-optimized hardware</div>
                </th>
                <th className="py-3 px-4 font-bold text-center w-1/4 text-brand-800 bg-brand-50/50">
                  <div className="text-sm">Balanced Tier ★</div>
                  <div className="text-[10px] font-normal text-gray-500">Recommended baseline</div>
                </th>
                <th className="py-3 px-4 font-bold text-center w-1/4 text-indigo-800 bg-indigo-50/50">
                  <div className="text-sm">High-Performance</div>
                  <div className="text-[10px] font-normal text-gray-500">Enterprise resiliency</div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50/60">
                  <td className="py-3 px-4 font-semibold text-gray-800">{row.label || row.metric}</td>
                  <td className="py-3 px-4 text-center text-gray-700 bg-emerald-50/20 font-medium">
                    {row.budget}
                  </td>
                  <td className="py-3 px-4 text-center font-bold text-brand-900 bg-brand-50/30">
                    {row.balanced}
                  </td>
                  <td className="py-3 px-4 text-center text-gray-800 bg-indigo-50/20 font-medium">
                    {row.high_performance}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

