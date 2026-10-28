import React from 'react'
import { SAMPLE_SCENARIOS } from '../utils/sampleScenarios'
import FreeTextBox from './FreeTextBox'

const DEPT_TYPES = [
  'office',
  'engineering',
  'finance',
  'hr',
  'management',
  'reception',
  'lab',
  'media',
  'datacenter_ops',
  'support',
]

const SECURITY_LEVELS = ['low', 'medium', 'high', 'critical']
const ORG_TYPES = ['school', 'hospital', 'it_company', 'corporate', 'government', 'other']
const REDUNDANCY_LEVELS = [
  { value: 'none', label: 'None (Single Core & Uplinks)' },
  { value: 'dual_uplink', label: 'Dual Uplink (Access Resiliency)' },
  { value: 'full_ha', label: 'Full HA (Redundant Core, HSRP, HA Firewalls)' },
]

export default function RequirementsForm({ values, onChange, onNext }) {
  const handleLoadScenario = (key) => {
    const sc = SAMPLE_SCENARIOS[key]
    if (sc) {
      onChange(JSON.parse(JSON.stringify(sc.data)))
    }
  }

  const updateField = (field, val) => {
    onChange({ ...values, [field]: val })
  }

  const updateServerField = (field, val) => {
    onChange({
      ...values,
      servers: { ...values.servers, [field]: parseInt(val) || 0 },
    })
  }

  const updateDept = (idx, field, val) => {
    const depts = [...values.departments]
    depts[idx] = { ...depts[idx], [field]: val }
    onChange({ ...values, departments: depts })
  }

  const addDept = () => {
    const newDept = {
      name: `Department ${values.departments.length + 1}`,
      users: 25,
      floor: 0,
      dept_type: 'office',
      security_level: 'medium',
      needs_guest_access: false,
      wired_printers: 1,
      notes: '',
    }
    onChange({ ...values, departments: [...values.departments, newDept] })
  }

  const removeDept = (idx) => {
    if (values.departments.length <= 1) return
    const depts = values.departments.filter((_, i) => i !== idx)
    onChange({ ...values, departments: depts })
  }

  return (
    <div className="space-y-8">
      {/* ── Free-Text AI Parser Box (Spec Section 9.1 & 13) ── */}
      <FreeTextBox onParsed={onChange} />

      {/* ── Demo Preset Bar ── */}
      <div className="bg-brand-50 border border-brand-100 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-brand-700">Quick-Load Demo Scenarios:</span>
          <p className="text-xs text-gray-500">Auto-fill standard test scenarios from the specification</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(SAMPLE_SCENARIOS).map(([key, sc]) => (
            <button
              key={key}
              type="button"
              onClick={() => handleLoadScenario(key)}
              className="bg-white border border-brand-200 hover:border-brand-500 text-brand-700 text-xs font-semibold px-3 py-1.5 rounded-lg shadow-sm hover:shadow transition"
            >
              ⚡ {sc.name}
            </button>
          ))}
        </div>
      </div>

      {/* ── Step 1 Form Cards ── */}
      <div className="bg-white border rounded-xl shadow-sm p-6 space-y-6">
        <h2 className="text-lg font-bold text-gray-800 border-b pb-3 flex items-center gap-2">
          🏢 1. Organization & Building Scope
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Organization Name</label>
            <input
              type="text"
              value={values.org_name}
              onChange={(e) => updateField('org_name', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              placeholder="e.g. Acme Corporation"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Organization Type</label>
            <select
              value={values.org_type}
              onChange={(e) => updateField('org_type', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none bg-white"
            >
              {ORG_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Building Floors</label>
            <input
              type="number"
              min="1"
              max="50"
              value={values.floors}
              onChange={(e) => updateField('floors', Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Internal Servers</label>
            <input
              type="number"
              min="0"
              value={values.servers?.count ?? 0}
              onChange={(e) => updateServerField('count', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Public-Facing (DMZ) Servers</label>
            <input
              type="number"
              min="0"
              value={values.servers?.public_facing ?? 0}
              onChange={(e) => updateServerField('public_facing', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Base IPv4 Pool</label>
            <input
              type="text"
              value={values.base_network}
              onChange={(e) => updateField('base_network', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-brand-500 outline-none"
              placeholder="10.0.0.0/16"
            />
          </div>
        </div>
      </div>

      {/* ── Network & Resiliency Parameters ── */}
      <div className="bg-white border rounded-xl shadow-sm p-6 space-y-6">
        <h2 className="text-lg font-bold text-gray-800 border-b pb-3 flex items-center gap-2">
          ⚡ 2. Connectivity, Bandwidth & Redundancy
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Internet Bandwidth (Mbps)</label>
            <input
              type="number"
              min="10"
              step="50"
              value={values.internet_bandwidth_mbps}
              onChange={(e) => updateField('internet_bandwidth_mbps', parseInt(e.target.value) || 100)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Redundancy Architecture</label>
            <select
              value={values.redundancy}
              onChange={(e) => updateField('redundancy', e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none bg-white font-medium"
            >
              {REDUNDANCY_LEVELS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Budget Limit (USD, optional)</label>
            <input
              type="number"
              min="0"
              step="1000"
              value={values.budget || ''}
              onChange={(e) => updateField('budget', e.target.value ? parseFloat(e.target.value) : null)}
              placeholder="e.g. 50000 (empty = unlimited)"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>
        </div>

        {/* Growth & Wireless Toggles */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pt-2 border-t">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Anticipated Growth (%)</label>
            <input
              type="number"
              min="0"
              max="200"
              value={values.growth_percent}
              onChange={(e) => updateField('growth_percent', parseFloat(e.target.value) || 0)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Horizon (Years)</label>
            <input
              type="number"
              min="1"
              max="10"
              value={values.growth_years}
              onChange={(e) => updateField('growth_years', parseInt(e.target.value) || 3)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>
          <div className="col-span-2 flex flex-wrap items-center gap-6 pt-5">
            <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={values.wifi_enabled}
                onChange={(e) => updateField('wifi_enabled', e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded"
              />
              Enable Enterprise Wi-Fi
            </label>
            <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={values.guest_wifi}
                onChange={(e) => updateField('guest_wifi', e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded"
              />
              Guest Wi-Fi VLAN
            </label>
            <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={values.remote_access_vpn}
                onChange={(e) => updateField('remote_access_vpn', e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded"
              />
              Remote VPN
            </label>
          </div>
        </div>
      </div>

      {/* ── Departments Table ── */}
      <div className="bg-white border rounded-xl shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between border-b pb-3">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            👥 3. Departments & Headcount ({values.departments.length})
          </h2>
          <button
            type="button"
            onClick={addDept}
            className="bg-brand-50 hover:bg-brand-100 text-brand-700 font-semibold text-xs px-3 py-1.5 rounded-lg border border-brand-200 transition"
          >
            + Add Department
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b text-gray-600">
                <th className="py-2.5 px-3 font-semibold">Dept Name</th>
                <th className="py-2.5 px-3 font-semibold w-24">Users</th>
                <th className="py-2.5 px-3 font-semibold w-20">Floor</th>
                <th className="py-2.5 px-3 font-semibold">Traffic Profile</th>
                <th className="py-2.5 px-3 font-semibold">Security Level</th>
                <th className="py-2.5 px-3 font-semibold w-20">Printers</th>
                <th className="py-2.5 px-3 font-semibold text-center w-16">Guest?</th>
                <th className="py-2.5 px-3 font-semibold text-center w-12">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {values.departments.map((d, idx) => (
                <tr key={idx} className="hover:bg-gray-50/50">
                  <td className="py-2 px-3">
                    <input
                      type="text"
                      value={d.name}
                      onChange={(e) => updateDept(idx, 'name', e.target.value)}
                      className="w-full border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-brand-500"
                      required
                    />
                  </td>
                  <td className="py-2 px-3">
                    <input
                      type="number"
                      min="1"
                      value={d.users}
                      onChange={(e) => updateDept(idx, 'users', parseInt(e.target.value) || 1)}
                      className="w-full border rounded px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="py-2 px-3">
                    <input
                      type="number"
                      min="0"
                      max={values.floors - 1}
                      value={d.floor}
                      onChange={(e) => updateDept(idx, 'floor', parseInt(e.target.value) || 0)}
                      className="w-full border rounded px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="py-2 px-3">
                    <select
                      value={d.dept_type}
                      onChange={(e) => updateDept(idx, 'dept_type', e.target.value)}
                      className="w-full border rounded px-2 py-1 text-xs bg-white capitalize"
                    >
                      {DEPT_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t.replace('_', ' ')}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-2 px-3">
                    <select
                      value={d.security_level}
                      onChange={(e) => updateDept(idx, 'security_level', e.target.value)}
                      className="w-full border rounded px-2 py-1 text-xs bg-white font-medium capitalize"
                    >
                      {SECURITY_LEVELS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-2 px-3">
                    <input
                      type="number"
                      min="0"
                      value={d.wired_printers}
                      onChange={(e) => updateDept(idx, 'wired_printers', parseInt(e.target.value) || 0)}
                      className="w-full border rounded px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="py-2 px-3 text-center">
                    <input
                      type="checkbox"
                      checked={d.needs_guest_access}
                      onChange={(e) => updateDept(idx, 'needs_guest_access', e.target.checked)}
                      className="w-3.5 h-3.5 text-brand-600 rounded"
                    />
                  </td>
                  <td className="py-2 px-3 text-center">
                    <button
                      type="button"
                      onClick={() => removeDept(idx)}
                      disabled={values.departments.length <= 1}
                      className="text-red-500 hover:text-red-700 disabled:opacity-25 font-bold text-sm"
                      title="Remove department"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Footer Navigation ── */}
      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={onNext}
          className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-6 py-2.5 rounded-lg shadow transition flex items-center gap-2"
        >
          Review Requirements →
        </button>
      </div>
    </div>
  )
}

