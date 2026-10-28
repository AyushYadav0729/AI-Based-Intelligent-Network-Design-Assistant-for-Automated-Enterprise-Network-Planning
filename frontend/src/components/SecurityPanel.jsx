import React from 'react'

export default function SecurityPanel({ security }) {
  const sec = security || {}
  const aclMatrix = sec.acl_matrix || {}
  const deptPolicies = sec.dept_policies || []
  const portSec = sec.port_security || {}
  const mgmt = sec.mgmt_hardening || {}

  const vlanKeys = Object.keys(aclMatrix)

  return (
    <div className="space-y-6">
      {/* ── Key Security Features ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Perimeter Defense</span>
          <div className="text-base font-bold text-gray-900 mt-1 flex items-center gap-2">
            <span className="text-emerald-500">🛡️</span> Stateful Next-Gen Firewall
          </div>
          <span className="text-xs text-gray-500">
            {sec.dmz_enabled ? 'DMZ Zone Segregated' : 'Standard Edge'}
          </span>
        </div>

        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Network Access Control</span>
          <div className="text-base font-bold text-gray-900 mt-1 flex items-center gap-2">
            <span className="text-blue-500">🔐</span> 802.1X & DAI
          </div>
          <span className="text-xs text-gray-500">DHCP Snooping Active</span>
        </div>

        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Port Security</span>
          <div className="text-base font-bold text-gray-900 mt-1 flex items-center gap-2">
            <span className="text-amber-500">🔒</span> Max {portSec.max_mac_addresses || 2} MACs / Port
          </div>
          <span className="text-xs text-gray-500">Action: {portSec.violation_action || 'restrict'}</span>
        </div>

        <div className="bg-white border p-4 rounded-xl shadow-sm">
          <span className="text-[11px] font-semibold text-gray-500 uppercase">Remote Access</span>
          <div className="text-base font-bold text-gray-900 mt-1 flex items-center gap-2">
            <span className="text-indigo-500">🌐</span> {sec.remote_access_vpn ? 'SSL/IPsec VPN' : 'Disabled'}
          </div>
          <span className="text-xs text-gray-500">NAT/PAT at Firewall</span>
        </div>
      </div>

      {/* ── Inter-VLAN ACL Matrix Heatmap ── */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b bg-gray-50/50 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-sm text-gray-800">Inter-VLAN ACL Matrix (Traffic Flow Policy)</h3>
            <p className="text-xs text-gray-500">Rows: Source VLANs → Columns: Destination VLANs</p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-emerald-500" /> Permit</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-amber-500" /> Limited (Ports)</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-rose-500" /> Deny</span>
          </div>
        </div>

        <div className="overflow-x-auto p-4">
          <table className="w-full text-center text-xs border-collapse font-sans">
            <thead>
              <tr>
                <th className="p-2 text-left font-bold text-gray-700 bg-gray-100/60 rounded-tl">Src \ Dst</th>
                {vlanKeys.map((dst) => (
                  <th key={dst} className="p-2 font-bold text-gray-700 bg-gray-100/60 min-w-[90px]">
                    {dst}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {vlanKeys.map((src) => (
                <tr key={src} className="hover:bg-gray-50/60">
                  <td className="p-2 text-left font-bold text-gray-800 bg-gray-50/80">{src}</td>
                  {vlanKeys.map((dst) => {
                    const rule = aclMatrix[src]?.[dst] || 'deny'
                    const isPermit = rule === 'permit'
                    const isDeny = rule === 'deny'

                    return (
                      <td key={dst} className="p-1.5">
                        <span
                          className={`inline-block w-full py-1 px-1.5 rounded text-[10px] font-bold uppercase transition ${
                            isPermit
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              : isDeny
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : 'bg-amber-100 text-amber-800 border border-amber-200'
                          }`}
                          title={`${src} → ${dst}: ${rule}`}
                        >
                          {rule.includes('limited') ? 'Limited' : rule}
                        </span>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Department Security Policies Table ── */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b bg-gray-50/50">
          <h3 className="font-bold text-sm text-gray-800">Department Security Controls & Hardening</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b text-gray-600">
                <th className="py-2.5 px-3 font-semibold">Department</th>
                <th className="py-2.5 px-3 font-semibold">Security Level</th>
                <th className="py-2.5 px-3 font-semibold text-center">802.1X Port Auth</th>
                <th className="py-2.5 px-3 font-semibold text-center">DHCP Snooping</th>
                <th className="py-2.5 px-3 font-semibold text-center">DAI (ARP Insp.)</th>
                <th className="py-2.5 px-3 font-semibold text-center">Direct Internet</th>
                <th className="py-2.5 px-3 font-semibold text-center">Syslog Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {deptPolicies.map((p, idx) => (
                <tr key={idx} className="hover:bg-gray-50/60">
                  <td className="py-2.5 px-3 font-semibold text-gray-800">{p.dept_name}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        p.security_level === 'critical'
                          ? 'bg-red-100 text-red-800'
                          : p.security_level === 'high'
                          ? 'bg-amber-100 text-amber-800'
                          : p.security_level === 'medium'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {p.security_level}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-center">{p.dot1x_enabled ? '✓ Enabled' : '—'}</td>
                  <td className="py-2.5 px-3 text-center">{p.dhcp_snooping ? '✓ Active' : '—'}</td>
                  <td className="py-2.5 px-3 text-center">{p.dai_enabled ? '✓ Active' : '—'}</td>
                  <td className="py-2.5 px-3 text-center">{p.direct_internet ? 'Permitted' : 'Blocked (Allowlist)'}</td>
                  <td className="py-2.5 px-3 text-center">{p.logging_enabled ? '✓ Central' : 'Standard'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

