import React from 'react'

export default function ValidationPanel({ validation }) {
  const issues = validation || []

  const errors = issues.filter((i) => i.severity === 'error')
  const warnings = issues.filter((i) => i.severity === 'warning')
  const infos = issues.filter((i) => i.severity === 'info')

  return (
    <div className="space-y-6">
      {/* ── Summary Banner ── */}
      {errors.length === 0 ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 flex items-center gap-4 text-emerald-900 shadow-sm">
          <div className="text-3xl">✅</div>
          <div>
            <h3 className="font-bold text-base">Network Design Formally Validated</h3>
            <p className="text-xs text-emerald-700 mt-0.5">
              All 21 deterministic network architecture rules passed with zero errors. Subnet addressing, VLAN mapping,
              port capacities, and security zones conform strictly to enterprise LAN design standards.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 flex items-center gap-4 text-rose-900 shadow-sm">
          <div className="text-3xl">❌</div>
          <div>
            <h3 className="font-bold text-base">{errors.length} Critical Validation Errors Detected</h3>
            <p className="text-xs text-rose-700 mt-0.5">
              The engine detected rule violations that prevent safe deployment. Please inspect the issues below.
            </p>
          </div>
        </div>
      )}

      {/* ── Issue Breakdown ── */}
      <div className="space-y-4">
        {/* Errors */}
        {errors.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-700 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-600" /> Errors ({errors.length})
            </h4>
            <div className="space-y-2">
              {errors.map((issue, idx) => (
                <div key={idx} className="bg-rose-50/70 border border-rose-200 rounded-lg p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-rose-800">{issue.code}</span>
                    {issue.related?.length > 0 && (
                      <span className="text-[10px] text-rose-600 font-mono">
                        Related: {issue.related.join(', ')}
                      </span>
                    )}
                  </div>
                  <p className="text-rose-900 font-medium">{issue.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500" /> Warnings & Capacity Notes ({warnings.length})
            </h4>
            <div className="space-y-2">
              {warnings.map((issue, idx) => (
                <div key={idx} className="bg-amber-50/70 border border-amber-200 rounded-lg p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-amber-800">{issue.code}</span>
                    {issue.related?.length > 0 && (
                      <span className="text-[10px] text-amber-600 font-mono">
                        Related: {issue.related.join(', ')}
                      </span>
                    )}
                  </div>
                  <p className="text-amber-900">{issue.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info */}
        {infos.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-blue-700 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500" /> Informational Notes ({infos.length})
            </h4>
            <div className="space-y-2">
              {infos.map((issue, idx) => (
                <div key={idx} className="bg-blue-50/70 border border-blue-200 rounded-lg p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-blue-800">{issue.code}</span>
                  </div>
                  <p className="text-blue-900">{issue.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

