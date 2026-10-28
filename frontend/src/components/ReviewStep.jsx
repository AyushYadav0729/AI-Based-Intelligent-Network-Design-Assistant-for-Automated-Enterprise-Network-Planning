import React from 'react'

export default function ReviewStep({ values, onBack, onGenerate, isGenerating }) {
  const totalUsers = values.departments.reduce((acc, d) => acc + (d.users || 0), 0)
  const growthFactor = 1.0 + (values.growth_percent || 0) / 100.0
  const plannedTotal = Math.ceil(totalUsers * growthFactor)

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="bg-white border rounded-xl shadow-sm p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{values.org_name}</h2>
            <p className="text-sm text-gray-500 capitalize">
              {values.org_type.replace('_', ' ')} · {values.floors} Floors · Private Pool: <code className="font-mono">{values.base_network}</code>
            </p>
          </div>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase bg-blue-100 text-blue-800">
            Review Step
          </span>
        </div>

        {/* ── Key Metrics Cards ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-3.5 rounded-lg border">
            <span className="text-xs font-semibold text-gray-500 uppercase">Headcount</span>
            <div className="text-lg font-bold text-gray-900 mt-1">
              {totalUsers} <span className="text-xs text-gray-400 font-normal">→ {plannedTotal} planned</span>
            </div>
            <span className="text-xs text-brand-600 font-medium">+{values.growth_percent}% / {values.growth_years} yrs</span>
          </div>

          <div className="bg-gray-50 p-3.5 rounded-lg border">
            <span className="text-xs font-semibold text-gray-500 uppercase">Redundancy</span>
            <div className="text-lg font-bold text-gray-900 mt-1 capitalize">
              {values.redundancy.replace('_', ' ')}
            </div>
            <span className="text-xs text-gray-500">{values.redundancy === 'full_ha' ? 'HSRP & HA Pairs' : 'Standard'}</span>
          </div>

          <div className="bg-gray-50 p-3.5 rounded-lg border">
            <span className="text-xs font-semibold text-gray-500 uppercase">Internet Bandwidth</span>
            <div className="text-lg font-bold text-gray-900 mt-1">{values.internet_bandwidth_mbps} Mbps</div>
            <span className="text-xs text-gray-500">{values.remote_access_vpn ? 'VPN Enabled' : 'No VPN'}</span>
          </div>

          <div className="bg-gray-50 p-3.5 rounded-lg border">
            <span className="text-xs font-semibold text-gray-500 uppercase">Servers</span>
            <div className="text-lg font-bold text-gray-900 mt-1">
              {values.servers?.count || 0} Int / {values.servers?.public_facing || 0} DMZ
            </div>
            <span className="text-xs text-gray-500">{values.servers?.public_facing > 0 ? 'DMZ Required' : 'No DMZ'}</span>
          </div>
        </div>
      </div>

      {/* ── Department Breakdown ── */}
      <div className="bg-white border rounded-xl shadow-sm p-6 space-y-4">
        <h3 className="text-base font-bold text-gray-800">Department Specifications</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b text-gray-600">
                <th className="py-2.5 px-3 font-semibold">Department</th>
                <th className="py-2.5 px-3 font-semibold">Current Users</th>
                <th className="py-2.5 px-3 font-semibold">Planned Users</th>
                <th className="py-2.5 px-3 font-semibold">Floor</th>
                <th className="py-2.5 px-3 font-semibold">Traffic Profile</th>
                <th className="py-2.5 px-3 font-semibold">Security Level</th>
                <th className="py-2.5 px-3 font-semibold">Printers</th>
                <th className="py-2.5 px-3 font-semibold">Guest Access</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {values.departments.map((d, i) => (
                <tr key={i} className="hover:bg-gray-50/50">
                  <td className="py-2.5 px-3 font-semibold text-gray-800">{d.name}</td>
                  <td className="py-2.5 px-3">{d.users}</td>
                  <td className="py-2.5 px-3 font-medium text-brand-700">
                    {Math.ceil(d.users * growthFactor)}
                  </td>
                  <td className="py-2.5 px-3">Floor {d.floor}</td>
                  <td className="py-2.5 px-3 capitalize">{d.dept_type.replace('_', ' ')}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        d.security_level === 'critical'
                          ? 'bg-red-100 text-red-800'
                          : d.security_level === 'high'
                          ? 'bg-amber-100 text-amber-800'
                          : d.security_level === 'medium'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {d.security_level}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">{d.wired_printers}</td>
                  <td className="py-2.5 px-3">{d.needs_guest_access ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Actions ── */}
      <div className="flex items-center justify-between gap-4 pt-2">
        <button
          type="button"
          onClick={onBack}
          className="border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold px-5 py-2.5 rounded-lg transition"
        >
          ← Edit Requirements
        </button>

        <button
          type="button"
          onClick={onGenerate}
          disabled={isGenerating}
          className="bg-brand-600 hover:bg-brand-700 text-white font-bold px-8 py-3 rounded-lg shadow-md hover:shadow-lg transition flex items-center gap-2 disabled:opacity-50"
        >
          {isGenerating ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Computing Deterministic Design...
            </>
          ) : (
            <>⚡ Generate Enterprise Design</>
          )}
        </button>
      </div>
    </div>
  )
}

