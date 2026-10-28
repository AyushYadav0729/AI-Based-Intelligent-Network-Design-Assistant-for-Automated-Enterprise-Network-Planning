import React, { useState } from 'react'

export default function IpVlanTable({ vlans, subnets, p2pLinks, capacity }) {
  const [activeView, setActiveView] = useState('subnets') // 'subnets' or 'capacity'

  // Map VLAN info with its subnet
  const vlanMap = (vlans || []).reduce((acc, v) => {
    acc[v.vlan_id] = v
    return acc
  }, {})

  return (
    <div className="space-y-6">
      {/* ── Sub-nav view selector ── */}
      <div className="flex items-center justify-between border-b pb-3">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setActiveView('subnets')}
            className={`text-xs font-bold px-4 py-2 rounded-lg transition ${
              activeView === 'subnets'
                ? 'bg-brand-600 text-white shadow'
                : 'bg-white border text-gray-700 hover:bg-gray-50'
            }`}
          >
            VLSM Subnets & VLANs ({subnets?.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveView('capacity')}
            className={`text-xs font-bold px-4 py-2 rounded-lg transition ${
              activeView === 'capacity'
                ? 'bg-brand-600 text-white shadow'
                : 'bg-white border text-gray-700 hover:bg-gray-50'
            }`}
          >
            Capacity Planning (Current vs Future)
          </button>
        </div>

        <span className="text-xs text-gray-500 font-mono">
          RFC 1918 Private Addressing
        </span>
      </div>

      {/* ── Main Subnets Table ── */}
      {activeView === 'subnets' ? (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b text-gray-600">
                  <th className="py-2.5 px-3 font-semibold">VLAN</th>
                  <th className="py-2.5 px-3 font-semibold">Subnet Name</th>
                  <th className="py-2.5 px-3 font-semibold font-mono">Network / Prefix</th>
                  <th className="py-2.5 px-3 font-semibold font-mono">Subnet Mask</th>
                  <th className="py-2.5 px-3 font-semibold font-mono">Gateway IP</th>
                  <th className="py-2.5 px-3 font-semibold font-mono">Usable Range</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Hosts</th>
                  <th className="py-2.5 px-3 font-semibold text-center w-36">Utilization</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(subnets || []).map((s, idx) => {
                  const v = s.vlan_id ? vlanMap[s.vlan_id] : null
                  const util = s.utilization_pct || 0
                  const isHigh = util > 85

                  return (
                    <tr key={idx} className="hover:bg-gray-50/60 font-sans">
                      <td className="py-2.5 px-3">
                        {s.vlan_id ? (
                          <span className="font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded border border-brand-200">
                            {s.vlan_id}
                          </span>
                        ) : (
                          <span className="text-gray-400 font-mono">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-gray-900">
                        {s.name}
                        {v?.dept && <span className="block text-[10px] text-gray-400 font-normal">{v.dept}</span>}
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-gray-800">
                        {s.network}/{s.prefix}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-gray-600">{s.mask}</td>
                      <td className="py-2.5 px-3 font-mono text-brand-700 font-semibold">
                        {s.gateway}
                        {s.hsrp && (
                          <span className="block text-[10px] text-indigo-600 font-normal">
                            HSRP: {s.hsrp.active} (Act) / {s.hsrp.standby} (Stby)
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-gray-600">
                        {s.first_host} – {s.last_host}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        <span className="font-bold text-gray-800">{s.required_hosts}</span>
                        <span className="text-gray-400 text-[10px]"> / {s.usable_hosts}</span>
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                isHigh ? 'bg-amber-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${Math.min(100, util)}%` }}
                            />
                          </div>
                          <span className={`text-[11px] font-bold w-10 text-right ${isHigh ? 'text-amber-600' : 'text-gray-700'}`}>
                            {util}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* ── Capacity Table ── */
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b text-gray-600">
                  <th className="py-2.5 px-3 font-semibold">Subnet</th>
                  <th className="py-2.5 px-3 font-semibold">Current Headcount</th>
                  <th className="py-2.5 px-3 font-semibold">Planned Headcount</th>
                  <th className="py-2.5 px-3 font-semibold">Subnet Host Capacity</th>
                  <th className="py-2.5 px-3 font-semibold">Utilization After Growth</th>
                  <th className="py-2.5 px-3 font-semibold">Max Headroom Before Exhaustion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {Object.entries(capacity || {}).map(([name, data], idx) => (
                  <tr key={idx} className="hover:bg-gray-50/60">
                    <td className="py-2.5 px-3 font-semibold text-gray-900">{name}</td>
                    <td className="py-2.5 px-3">{data.current_hosts} hosts</td>
                    <td className="py-2.5 px-3 font-medium text-brand-700">{data.planned_hosts} hosts</td>
                    <td className="py-2.5 px-3 font-bold text-gray-800">{data.usable_hosts} hosts</td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-gray-800">{data.utilization_pct}%</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        +{data.max_growth_percent_before_exhaustion}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Point-to-Point Links ── */}
      {p2pLinks && p2pLinks.length > 0 && (
        <div className="bg-white border rounded-xl shadow-sm p-4 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700 flex items-center gap-2">
            🔗 Point-to-Point Interconnect Blocks (/30)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {p2pLinks.map((p, i) => (
              <div key={i} className="bg-gray-50 border p-2.5 rounded-lg text-xs space-y-1">
                <span className="font-bold text-gray-800">{p.name}</span>
                <div className="font-mono text-gray-600">{p.network}/{p.prefix}</div>
                <div className="font-mono text-[11px] text-gray-400">
                  Endpoints: {p.first_host} ↔ {p.last_host}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

