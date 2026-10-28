import React from 'react'

export default function DevicesCostTable({ devices, cost }) {
  const c = cost || {}
  const items = devices || []

  return (
    <div className="space-y-6">
      {/* ── Cost Summary Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Hardware Units</span>
          <div className="text-xl font-bold text-gray-900 mt-1">
            ${(c.devices_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <span className="text-xs text-gray-400">{items.reduce((acc, d) => acc + d.quantity, 0)} devices</span>
        </div>

        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Software / Threat Lic.</span>
          <div className="text-xl font-bold text-gray-900 mt-1">
            ${(c.licenses_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <span className="text-xs text-gray-400">Firewall & Security</span>
        </div>

        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Structured Cabling</span>
          <div className="text-xl font-bold text-gray-900 mt-1">
            ${(c.cabling_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <span className="text-xs text-gray-400">$150 / user drop</span>
        </div>

        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Rack & Power/UPS</span>
          <div className="text-xl font-bold text-gray-900 mt-1">
            ${(c.rack_ups_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <span className="text-xs text-gray-400">$2,000 allowance/unit</span>
        </div>

        <div className="bg-brand-50 border border-brand-200 p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-bold text-brand-700 uppercase">Total Project Cost</span>
          <div className="text-2xl font-black text-brand-900 mt-1">
            ${(c.total_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <span className="text-xs font-semibold">
            {c.budget ? (
              c.within_budget ? (
                <span className="text-emerald-700">✓ Within ${c.budget.toLocaleString()} budget</span>
              ) : (
                <span className="text-rose-600">⚠ Over ${c.budget.toLocaleString()} budget</span>
              )
            ) : (
              <span className="text-gray-500">No budget cap</span>
            )}
          </span>
        </div>
      </div>

      {/* ── Devices Inventory Table ── */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b bg-gray-50/50 flex items-center justify-between">
          <h3 className="font-bold text-sm text-gray-800">Hardware BOM (Bill of Materials)</h3>
          <span className="text-xs text-gray-500">Catalog Pricing Baseline ({c.currency || 'USD'})</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b text-gray-600">
                <th className="py-2.5 px-3 font-semibold">Role</th>
                <th className="py-2.5 px-3 font-semibold">Hardware Model</th>
                <th className="py-2.5 px-3 font-semibold">Deployed Location</th>
                <th className="py-2.5 px-3 font-semibold text-center w-20">Quantity</th>
                <th className="py-2.5 px-3 font-semibold text-right w-28">Unit Price</th>
                <th className="py-2.5 px-3 font-semibold text-right w-32">Total Price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((dev, idx) => (
                <tr key={idx} className="hover:bg-gray-50/60">
                  <td className="py-2.5 px-3">
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gray-100 text-gray-700">
                      {dev.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-gray-900">{dev.model}</td>
                  <td className="py-2.5 px-3 text-gray-600">{dev.location}</td>
                  <td className="py-2.5 px-3 text-center font-bold text-gray-800">{dev.quantity}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-gray-600">
                    ${dev.unit_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold text-brand-700">
                    ${dev.total_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
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

