/**
 * TopologyDiagram.jsx — Authentic Cisco Packet Tracer Network Topology Visualizer.
 * Spec Section 13 & Cisco Packet Tracer Design Language.
 *
 * Features:
 *  - Authentic Cisco Vector Icons (Router cylinder, L3 Core Switch cube, L2 Switch with arrows,
 *    ASA/Firepower brick firewall, WAN Cloud, UCS Server blade, AP dome, Workstation PC).
 *  - Packet Tracer Green Link Lights (▲ indicators at interface endpoints).
 *  - Real interface port labels (Gi0/0/0, Te1/0/1, Fa0/1, Po1).
 *  - Authentic Packet Tracer Light Grid Canvas with Dark NOC Console toggle.
 *  - Simulation / Realtime animated packet transmission toggle.
 *  - Packet Tracer Device Inspector Modal with Physical Chassis, Interface Table, and Cisco IOS CLI tabs.
 *  - High-res PNG export with html-to-image.
 */
import React, { useMemo, useState, useCallback, useRef } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  MarkerType,
  applyNodeChanges,
  applyEdgeChanges,
} from 'reactflow'
import 'reactflow/dist/style.css'

// ── Cisco Device Vector SVGs (Pixel-perfect Packet Tracer Style) ──────────────

export function CiscoCloudIcon({ className = 'w-16 h-12' }) {
  return (
    <svg viewBox="0 0 100 64" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="cloudGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="100%" stopColor="#0284c7" />
        </linearGradient>
        <filter id="ciscoGlow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.2" />
        </filter>
      </defs>
      {/* Cloud Outline */}
      <path
        d="M26 48h48c9 0 16-7 16-16 0-8-6-14-14-15-2-10-10-17-21-17-8 0-16 5-19 12-3-2-6-3-10-3-9 0-16 7-16 16 0 1 0 2 .2 3C7 33 2 39 2 46c0 9 7 16 16 16h8z"
        fill="url(#cloudGrad)"
        stroke="#0369a1"
        strokeWidth="2"
        filter="url(#ciscoGlow)"
      />
      {/* Network Globe Lines inside Cloud */}
      <ellipse cx="50" cy="32" rx="20" ry="14" stroke="#ffffff" strokeWidth="1.2" strokeOpacity="0.7" fill="none" />
      <ellipse cx="50" cy="32" rx="8" ry="14" stroke="#ffffff" strokeWidth="1.2" strokeOpacity="0.7" fill="none" />
      <line x1="30" y1="32" x2="70" y2="32" stroke="#ffffff" strokeWidth="1.2" strokeOpacity="0.7" />
      {/* WAN Lightning/Arrow */}
      <path d="M48 24l-4 8h6l-3 8 9-10h-6l4-6h-6z" fill="#facc15" />
    </svg>
  )
}

export function CiscoRouterIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="rtrTop" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="100%" stopColor="#0284c7" />
        </linearGradient>
        <linearGradient id="rtrBody" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#0369a1" />
          <stop offset="100%" stopColor="#075985" />
        </linearGradient>
      </defs>
      {/* Cylindrical Base */}
      <path d="M10 38v18c0 9 13.4 16 30 16s30-7 30-16V38" fill="url(#rtrBody)" stroke="#0c4a6e" strokeWidth="2" />
      {/* Top Ellipse Face */}
      <ellipse cx="40" cy="38" rx="30" ry="16" fill="url(#rtrTop)" stroke="#0c4a6e" strokeWidth="2" />
      {/* 4 Radial Cisco Arrows (2 Inward, 2 Outward) */}
      <g stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="#ffffff">
        {/* Arrow Left (Pointing In) */}
        <line x1="18" y1="38" x2="28" y2="38" />
        <polygon points="28,34 33,38 28,42" />
        {/* Arrow Right (Pointing In) */}
        <line x1="62" y1="38" x2="52" y2="38" />
        <polygon points="52,34 47,38 52,42" />
        {/* Arrow Top (Pointing Out) */}
        <line x1="40" y1="34" x2="40" y2="28" />
        <polygon points="36,29 40,24 44,29" />
        {/* Arrow Bottom (Pointing Out) */}
        <line x1="40" y1="42" x2="40" y2="48" />
        <polygon points="36,47 40,52 44,47" />
      </g>
      {/* Front Panel Link Activity LEDs */}
      <circle cx="28" cy="62" r="2.2" fill="#22c55e" />
      <circle cx="36" cy="62" r="2.2" fill="#22c55e" />
      <circle cx="44" cy="62" r="2.2" fill="#22c55e" />
      <circle cx="52" cy="62" r="2.2" fill="#facc15" />
    </svg>
  )
}

export function CiscoCoreSwitchIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="coreTop" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#4338ca" />
        </linearGradient>
        <linearGradient id="coreFront" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#3730a3" />
          <stop offset="100%" stopColor="#312e81" />
        </linearGradient>
      </defs>
      {/* 3D Multilayer Switch Chassis */}
      <path d="M12 28L40 14L68 28L40 42Z" fill="url(#coreTop)" stroke="#1e1b4b" strokeWidth="2" />
      <path d="M12 28L40 42V66L12 52Z" fill="url(#coreFront)" stroke="#1e1b4b" strokeWidth="2" />
      <path d="M68 28L40 42V66L68 52Z" fill="#312e81" stroke="#1e1b4b" strokeWidth="2" />
      {/* Multilayer 4-Way Cross Arrows (Cisco L3 Symbol) */}
      <g stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="#ffffff">
        <path d="M28 28L36 24M44 32L52 28M36 32L28 36M44 24L52 28" />
        <polygon points="34,22 40,24 37,28" />
        <polygon points="46,34 40,32 43,28" />
        <polygon points="26,33 26,38 31,37" />
        <polygon points="54,23 54,28 49,27" />
      </g>
      {/* Front Panel QSFP Port Grills */}
      <rect x="18" y="46" width="6" height="4" rx="1" fill="#22c55e" />
      <rect x="26" y="46" width="6" height="4" rx="1" fill="#22c55e" />
      <rect x="18" y="52" width="6" height="4" rx="1" fill="#22c55e" />
      <rect x="26" y="52" width="6" height="4" rx="1" fill="#38bdf8" />
      <rect x="46" y="46" width="16" height="3" rx="1" fill="#1e1b4b" />
      <rect x="46" y="51" width="16" height="3" rx="1" fill="#1e1b4b" />
    </svg>
  )
}

export function CiscoAccessSwitchIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="swTop" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#10b981" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>
        <linearGradient id="swFront" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#047857" />
          <stop offset="100%" stopColor="#065f46" />
        </linearGradient>
      </defs>
      {/* 3D Switch Chassis */}
      <path d="M10 32L38 20L70 32L42 44Z" fill="url(#swTop)" stroke="#064e3b" strokeWidth="2" />
      <path d="M10 32L42 44V60L10 48Z" fill="url(#swFront)" stroke="#064e3b" strokeWidth="2" />
      <path d="M70 32L42 44V60L70 48Z" fill="#065f46" stroke="#064e3b" strokeWidth="2" />
      {/* Dual Opposite Direction Arrows (Cisco Switch Symbol) */}
      <g stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="#ffffff">
        <line x1="26" y1="30" x2="48" y2="30" />
        <polygon points="46,26 53,30 46,34" />
        <line x1="54" y1="34" x2="32" y2="34" />
        <polygon points="34,38 27,34 34,30" />
      </g>
      {/* 24-Port RJ-45 Matrix Grill with Activity LEDs */}
      <circle cx="16" cy="42" r="1.5" fill="#4ade80" />
      <circle cx="21" cy="42" r="1.5" fill="#4ade80" />
      <circle cx="26" cy="42" r="1.5" fill="#4ade80" />
      <circle cx="31" cy="42" r="1.5" fill="#4ade80" />
      <circle cx="36" cy="42" r="1.5" fill="#facc15" />
      <rect x="47" y="47" width="18" height="4" rx="1" fill="#022c22" />
    </svg>
  )
}

export function CiscoDistSwitchIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="distTop" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#14b8a6" />
          <stop offset="100%" stopColor="#0d9488" />
        </linearGradient>
        <linearGradient id="distFront" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#0f766e" />
          <stop offset="100%" stopColor="#115e59" />
        </linearGradient>
      </defs>
      <path d="M10 32L38 20L70 32L42 44Z" fill="url(#distTop)" stroke="#134e4a" strokeWidth="2" />
      <path d="M10 32L42 44V60L10 48Z" fill="url(#distFront)" stroke="#134e4a" strokeWidth="2" />
      <path d="M70 32L42 44V60L70 48Z" fill="#115e59" stroke="#134e4a" strokeWidth="2" />
      <g stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="#ffffff">
        <line x1="24" y1="32" x2="40" y2="28" />
        <polygon points="38,25 45,28 40,32" />
        <line x1="56" y1="32" x2="40" y2="36" />
        <polygon points="42,39 35,36 40,32" />
      </g>
      <circle cx="16" cy="42" r="1.5" fill="#2dd4bf" />
      <circle cx="22" cy="42" r="1.5" fill="#2dd4bf" />
      <circle cx="28" cy="42" r="1.5" fill="#2dd4bf" />
    </svg>
  )
}

export function CiscoFirewallIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="fwGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ef4444" />
          <stop offset="100%" stopColor="#b91c1c" />
        </linearGradient>
      </defs>
      {/* Brick Wall Firewall Chassis */}
      <rect x="12" y="18" width="56" height="44" rx="4" fill="url(#fwGrad)" stroke="#7f1d1d" strokeWidth="2" />
      {/* Brick Mortar Grid */}
      <g stroke="#ffffff" strokeWidth="1.5" strokeOpacity="0.8">
        <line x1="12" y1="29" x2="68" y2="29" />
        <line x1="12" y1="40" x2="68" y2="40" />
        <line x1="12" y1="51" x2="68" y2="51" />
        {/* Row 1 bricks */}
        <line x1="26" y1="18" x2="26" y2="29" />
        <line x1="42" y1="18" x2="42" y2="29" />
        <line x1="56" y1="18" x2="56" y2="29" />
        {/* Row 2 bricks */}
        <line x1="19" y1="29" x2="19" y2="40" />
        <line x1="34" y1="29" x2="34" y2="40" />
        <line x1="50" y1="29" x2="50" y2="40" />
        <line x1="62" y1="29" x2="62" y2="40" />
        {/* Row 3 bricks */}
        <line x1="26" y1="40" x2="26" y2="51" />
        <line x1="42" y1="40" x2="42" y2="51" />
        <line x1="56" y1="40" x2="56" y2="51" />
      </g>
      {/* Security Shield Center Emblem */}
      <path
        d="M40 28c4 0 8-3 8-3v9c0 5-4 9-8 11-4-2-8-6-8-11v-9s4 3 8 3z"
        fill="#ffffff"
        stroke="#7f1d1d"
        strokeWidth="1.5"
      />
      <circle cx="40" cy="36" r="2.5" fill="#ef4444" />
      {/* Dual Port Link Indicators */}
      <circle cx="20" cy="56" r="2" fill="#22c55e" />
      <circle cx="60" cy="56" r="2" fill="#22c55e" />
    </svg>
  )
}

export function CiscoServerIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="srvGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#334155" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      {/* 2U Rack Blade Chassis */}
      <rect x="10" y="20" width="60" height="42" rx="3" fill="url(#srvGrad)" stroke="#475569" strokeWidth="2" />
      {/* 4 Hot-Swap Drive Bays */}
      <rect x="15" y="25" width="22" height="7" rx="1" fill="#1e293b" stroke="#64748b" strokeWidth="1" />
      <circle cx="18" cy="28.5" r="1.2" fill="#22c55e" />
      <rect x="15" y="35" width="22" height="7" rx="1" fill="#1e293b" stroke="#64748b" strokeWidth="1" />
      <circle cx="18" cy="38.5" r="1.2" fill="#22c55e" />
      <rect x="15" y="45" width="22" height="7" rx="1" fill="#1e293b" stroke="#64748b" strokeWidth="1" />
      <circle cx="18" cy="48.5" r="1.2" fill="#f59e0b" />
      {/* Ventilation Grille & Power / NIC LEDs */}
      <g fill="#475569">
        <rect x="42" y="25" width="22" height="2" rx="0.5" />
        <rect x="42" y="29" width="22" height="2" rx="0.5" />
        <rect x="42" y="33" width="22" height="2" rx="0.5" />
      </g>
      <circle cx="45" cy="44" r="2.5" fill="#22c55e" />
      <circle cx="53" cy="44" r="2" fill="#38bdf8" />
      <circle cx="60" cy="44" r="2" fill="#facc15" />
      <rect x="42" y="50" width="22" height="6" rx="1" fill="#0284c7" fillOpacity="0.4" />
      <text x="44" y="54.5" fontSize="4" fill="#38bdf8" fontWeight="bold">UCS C220</text>
    </svg>
  )
}

export function CiscoApIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Circular AP Dome */}
      <circle cx="40" cy="42" r="24" fill="#ffffff" stroke="#0891b2" strokeWidth="2.5" />
      <circle cx="40" cy="42" r="18" fill="#f0fdfa" stroke="#cbd5e1" strokeWidth="1" />
      {/* Tri-Color Cisco Status Ring */}
      <circle cx="40" cy="42" r="5" fill="#06b6d4" />
      <circle cx="40" cy="42" r="2.5" fill="#ffffff" />
      {/* Radiating RF Signal Wave Arcs */}
      <path d="M22 24a26 26 0 0 1 36 0" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M27 29a19 19 0 0 1 26 0" stroke="#0891b2" strokeWidth="2" strokeLinecap="round" />
      <path d="M32 34a12 12 0 0 1 16 0" stroke="#0e7490" strokeWidth="1.5" strokeLinecap="round" />
      {/* RJ-45 PoE Uplink Indicator */}
      <rect x="36" y="64" width="8" height="5" rx="1" fill="#334155" />
      <circle cx="40" cy="66.5" r="1" fill="#22c55e" />
    </svg>
  )
}

export function CiscoWlcIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="10" y="24" width="60" height="34" rx="3" fill="#0284c7" stroke="#0369a1" strokeWidth="2" />
      {/* Antenna Waves */}
      <path d="M20 18l6 6M60 18l-6 6" stroke="#facc15" strokeWidth="2" strokeLinecap="round" />
      <circle cx="40" cy="41" r="8" fill="#ffffff" />
      <circle cx="40" cy="41" r="4" fill="#0284c7" />
      <rect x="16" y="48" width="10" height="4" rx="1" fill="#082f49" />
      <rect x="54" y="48" width="10" height="4" rx="1" fill="#082f49" />
      <circle cx="21" cy="50" r="1" fill="#22c55e" />
      <circle cx="59" cy="50" r="1" fill="#22c55e" />
    </svg>
  )
}

export function CiscoPcIcon({ className = 'w-14 h-14' }) {
  return (
    <svg viewBox="0 0 80 80" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Monitor Display */}
      <rect x="16" y="16" width="48" height="32" rx="3" fill="#1e293b" stroke="#475569" strokeWidth="2" />
      {/* Screen area with simulated Cisco CLI terminal */}
      <rect x="20" y="20" width="40" height="24" fill="#020617" />
      <line x1="24" y1="25" x2="36" y2="25" stroke="#22c55e" strokeWidth="1.5" />
      <line x1="24" y1="30" x2="48" y2="30" stroke="#94a3b8" strokeWidth="1" />
      <line x1="24" y1="35" x2="42" y2="35" stroke="#94a3b8" strokeWidth="1" />
      {/* Monitor Stand & Base */}
      <path d="M36 48h8v6h-8z" fill="#475569" />
      <path d="M30 54h20v2H30z" fill="#334155" />
      {/* Desktop Tower (Classic Packet Tracer Workstation) */}
      <rect x="52" y="28" width="16" height="28" rx="2" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
      <circle cx="60" cy="34" r="2" fill="#22c55e" />
      <rect x="56" y="40" width="8" height="2" fill="#475569" />
      <circle cx="60" cy="48" r="1.5" fill="#38bdf8" />
    </svg>
  )
}

// ── Custom React Flow Node: Cisco Packet Tracer Device ────────────────────────

export function CiscoDeviceNode({ data, selected }) {
  const { raw, showPorts, showSubnets, isDark } = data
  const type = raw.type || 'access'

  const renderIcon = () => {
    switch (type) {
      case 'internet':
        return <CiscoCloudIcon className="w-16 h-12" />
      case 'router':
        return <CiscoRouterIcon className="w-14 h-14" />
      case 'firewall':
        return <CiscoFirewallIcon className="w-14 h-14" />
      case 'core':
        return <CiscoCoreSwitchIcon className="w-14 h-14" />
      case 'distribution':
        return <CiscoDistSwitchIcon className="w-14 h-14" />
      case 'access':
        return <CiscoAccessSwitchIcon className="w-14 h-14" />
      case 'server_switch':
        return <CiscoCoreSwitchIcon className="w-14 h-14" />
      case 'server':
        return <CiscoServerIcon className="w-14 h-14" />
      case 'wlc':
        return <CiscoWlcIcon className="w-14 h-14" />
      case 'ap':
        return <CiscoApIcon className="w-14 h-14" />
      case 'endpoint':
      default:
        return <CiscoPcIcon className="w-14 h-14" />
    }
  }

  return (
    <div
      className={`group relative flex flex-col items-center p-2 rounded-xl transition-all duration-150 cursor-pointer ${selected
          ? 'ring-2 ring-brand-500 shadow-xl scale-105'
          : 'hover:scale-105 hover:drop-shadow-md'
        }`}
      style={{ minWidth: '150px' }}
    >
      {/* Connection Handles (Bidirectional) */}
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-brand-500 !border-white" />
      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-brand-500 !border-white" />
      <Handle type="target" position={Position.Left} id="left" className="!w-2 !h-2 !bg-brand-500 !border-white" />
      <Handle type="source" position={Position.Right} id="right" className="!w-2 !h-2 !bg-brand-500 !border-white" />

      {/* Packet Tracer Device Icon */}
      <div className="relative flex items-center justify-center p-1">
        {renderIcon()}

        {/* Cisco Green Link Status LED */}
        <span
          className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white shadow-sm animate-pulse"
          title="Interface Up / Line Protocol Up"
        />
      </div>

      {/* Device Typography Badge (Authentic Packet Tracer Labeling) */}
      <div className="mt-1 text-center select-none">
        <div
          className={`font-mono font-bold text-xs leading-tight tracking-tight ${isDark ? 'text-slate-100' : 'text-slate-900'
            }`}
        >
          {raw.label}
        </div>

        {/* Catalog Model */}
        <div
          className={`text-[10px] font-medium leading-tight truncate max-w-[140px] ${isDark ? 'text-slate-400' : 'text-slate-500'
            }`}
        >
          {raw.model || raw.type}
        </div>

        {/* Optional Floor / Location Pill */}
        {raw.floor && (
          <span className="inline-block mt-0.5 text-[9px] font-bold px-1.5 py-0.2 rounded bg-brand-50 text-brand-700 border border-brand-200">
            {raw.floor}
          </span>
        )}
      </div>
    </div>
  )
}

const nodeTypes = {
  ciscoDevice: CiscoDeviceNode,
}

// ── Packet Tracer Device Inspector Modal ──────────────────────────────────────

function PacketTracerInspector({ node, onClose, subnets, vlans }) {
  const [activeTab, setActiveTab] = useState('physical')

  if (!node) return null

  // Generate authentic Cisco IOS show command outputs based on device role
  const getCiscoCliText = () => {
    const isCore = node.type === 'core'
    const isAccess = node.type === 'access'
    const isFw = node.type === 'firewall'
    const isRtr = node.type === 'router'

    if (isCore) {
      return `CORE-SW# show ip route ospf
Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       O - OSPF, IA - OSPF inter area, N1 - OSPF NSSA external type 1

Gateway of last resort is 10.0.0.1 to network 0.0.0.0

O    10.0.1.0/24 [110/2] via 10.0.254.2, 00:14:22, TenGigabitEthernet1/0/1
O    10.0.2.0/24 [110/2] via 10.0.254.6, 00:14:22, TenGigabitEthernet1/0/2
O    10.0.3.0/24 [110/2] via 10.0.254.10, 00:14:22, TenGigabitEthernet1/0/3
O    10.0.8.0/28 [110/1] via 10.0.254.14, 00:14:22, Vlan999

CORE-SW# show vlan brief
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Te1/0/1-24, Fo1/0/1-4
10   OFFICE-DATA                      active    Vlan10
20   VOICE                            active    Vlan20
30   SERVERS                          active    Vlan30
999  MANAGEMENT                       active    Vlan999

CORE-SW# show standby brief
                     P indicates configured to preempt.
                     |
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Vl10        10   110 P Active  local           10.0.1.3        10.0.1.1
Vl20        20   110 P Active  local           10.0.2.3        10.0.2.1`
    }

    if (isFw) {
      return `ciscoasa# show access-list
access-list OUTSIDE_IN; 4 elements; name hash: 0x8a92fbc1
access-list OUTSIDE_IN line 1 extended permit tcp any host 10.0.100.10 eq https (hitcnt=1420)
access-list OUTSIDE_IN line 2 extended permit tcp any host 10.0.100.10 eq http (hitcnt=310)
access-list OUTSIDE_IN line 3 extended permit icmp any any echo-reply (hitcnt=45)
access-list OUTSIDE_IN line 4 extended deny ip any any log (hitcnt=2890)

ciscoasa# show nat
Auto NAT Policies (Section 2)
1 (INSIDE) to (OUTSIDE) source dynamic any interface
    translate_hits = 15890, untranslate_hits = 840`
    }

    if (isAccess) {
      return `ACC-SW# show interfaces status
Port      Name               Status       Vlan       Duplex  Speed Type
Fa0/1     Client Host        connected    10         a-full  a-100 10/100BaseTX
Fa0/2     Client Host        connected    10         a-full  a-100 10/100BaseTX
Fa0/24    Ceiling AP (PoE)   connected    trunk      a-full a-1000 10/100BaseTX
Gi1/0/49  UPLINK-TO-CORE     connected    trunk      full    1000 1000BaseTX
Gi1/0/50  UPLINK-TO-CORE-2   connected    trunk      full    1000 1000BaseTX

ACC-SW# show port-security
Secure Port  MaxSecureAddr  CurrentAddr  SecurityViolation  Security Action
-----------  -------------  -----------  -----------------  ---------------
Fa0/1                    2            1                  0         Restrict
Fa0/2                    2            1                  0         Restrict`
    }

    return `${node.label}# show version
Cisco IOS Software, IOS-XE Software, Version 17.09.04a
Technical Support: http://www.cisco.com/techsupport
Model: ${node.model || 'Cisco Enterprise Device'}
System serial number: FOC2419U0AB
Uptime is 4 weeks, 2 days, 16 hours, 4 minutes`
  }

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Packet Tracer Window Header */}
        <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" />
              <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
              <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
            </div>
            <span className="font-mono text-xs font-bold text-slate-200">
              Cisco Packet Tracer — [{node.label}]
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white font-bold text-sm px-2 py-0.5 rounded transition"
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="bg-slate-100 border-b border-slate-200 px-4 pt-2 flex gap-2 text-xs font-bold">
          {[
            { id: 'physical', label: '🔌 Physical Chassis' },
            { id: 'config', label: '⚙️ Configuration & Ports' },
            { id: 'cli', label: '💻 Cisco IOS CLI' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-3.5 rounded-t-lg transition border-b-2 ${activeTab === tab.id
                  ? 'bg-white border-brand-600 text-brand-700 shadow-sm'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-5 max-h-[460px] overflow-y-auto text-xs">
          {activeTab === 'physical' && (
            <div className="space-y-4">
              <div className="bg-slate-900 rounded-xl p-4 border border-slate-700 text-white space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-emerald-400 font-bold">CISCO SYSTEMS</span>
                    <span className="text-slate-400">|</span>
                    <span className="text-slate-200 font-semibold">{node.model}</span>
                  </div>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                    ● Dual PSU: OK
                  </span>
                </div>

                {/* Simulated Front-Panel Port Lights */}
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                  <div className="text-[10px] text-slate-400 font-mono">10/100/1000 GigabitEthernet Port Matrix</div>
                  <div className="grid grid-cols-12 gap-1.5 py-1">
                    {Array.from({ length: 24 }).map((_, i) => (
                      <div
                        key={i}
                        className={`h-4 rounded flex items-center justify-center text-[8px] font-mono font-bold ${i < 6 || i === 23
                            ? 'bg-emerald-500 text-slate-950 shadow-[0_0_8px_rgba(34,197,94,0.6)]'
                            : 'bg-slate-800 text-slate-500'
                          }`}
                        title={`Port Gi1/0/${i + 1}: ${i < 6 || i === 23 ? 'Link Up (1000M)' : 'No Link'}`}
                      >
                        {i + 1}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 text-slate-300 pt-1">
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase font-bold">Role</span>
                    <span className="font-semibold text-slate-100 capitalize">{node.type}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase font-bold">Location</span>
                    <span className="font-semibold text-slate-100">{node.floor || 'Main DC / Rack'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase font-bold">Console Baud</span>
                    <span className="font-semibold text-slate-100">9600 8-N-1</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'config' && (
            <div className="space-y-4">
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <span className="font-bold text-slate-700 block mb-1">Device Parameters</span>
                <div className="grid grid-cols-2 gap-2 text-slate-600">
                  <div><span className="text-slate-400">Hostname:</span> <code className="text-brand-700 font-bold">{node.label}</code></div>
                  <div><span className="text-slate-400">Hardware:</span> {node.model}</div>
                  <div><span className="text-slate-400">Layer:</span> {node.layer} tier</div>
                  <div><span className="text-slate-400">Status:</span> <span className="text-emerald-700 font-semibold">In Service</span></div>
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1.5">Connected Interfaces & Ports</span>
                <table className="w-full border-collapse border border-slate-200 rounded-lg overflow-hidden text-left text-xs">
                  <thead className="bg-slate-100 text-slate-700">
                    <tr>
                      <th className="p-2 border">Port</th>
                      <th className="p-2 border">Speed</th>
                      <th className="p-2 border">Duplex</th>
                      <th className="p-2 border">VLAN Mode</th>
                      <th className="p-2 border">Link Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    <tr>
                      <td className="p-2 font-mono font-bold text-brand-700">Gi1/0/1</td>
                      <td className="p-2">1000 Mbps</td>
                      <td className="p-2">Full</td>
                      <td className="p-2 font-semibold">Trunk (802.1Q)</td>
                      <td className="p-2 text-emerald-600 font-bold">● Connected</td>
                    </tr>
                    <tr>
                      <td className="p-2 font-mono font-bold text-brand-700">Gi1/0/2</td>
                      <td className="p-2">1000 Mbps</td>
                      <td className="p-2">Full</td>
                      <td className="p-2 font-semibold">VLAN 10 [DATA]</td>
                      <td className="p-2 text-emerald-600 font-bold">● Connected</td>
                    </tr>
                    <tr>
                      <td className="p-2 font-mono font-bold text-brand-700">Te1/0/1</td>
                      <td className="p-2">10 Gbps SFP+</td>
                      <td className="p-2">Full</td>
                      <td className="p-2 font-semibold">Uplink Trunk</td>
                      <td className="p-2 text-emerald-600 font-bold">● Connected</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'cli' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-slate-500 text-[11px]">
                <span>Cisco IOS Command Line Interface (CLI)</span>
                <span className="font-mono text-emerald-600">Terminal Ready</span>
              </div>
              <div className="bg-slate-950 text-emerald-400 font-mono text-[11px] p-4 rounded-xl border border-slate-800 leading-relaxed overflow-x-auto shadow-inner select-text">
                <pre>{getCiscoCliText()}</pre>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="bg-slate-50 px-4 py-3 border-t border-slate-200 flex justify-between items-center text-xs">
          <span className="text-slate-500">Click any other device to inspect.</span>
          <button
            type="button"
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-900 text-white font-bold px-4 py-1.5 rounded-lg shadow-sm transition"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main TopologyDiagram Component ──────────────────────────────────────────

export default function TopologyDiagram({
  graph,
  topologyName,
  vlans = [],
  subnets = [],
  devices = [],
  routing = {},
  onSnapshot,
}) {
  const [selectedNode, setSelectedNode] = useState(null)
  const [isDark, setIsDark] = useState(false)
  const [showPorts, setShowPorts] = useState(true)
  const [showSpeeds, setShowSpeeds] = useState(true)
  const [showEndpoints, setShowEndpoints] = useState(true)
  const [simulationMode, setSimulationMode] = useState(false)
  const diagramRef = useRef(null)

  // Auto-capture high-res snapshot for ExportPanel and PDF embedding
  React.useEffect(() => {
    if (!diagramRef.current || !onSnapshot) return
    const timer = setTimeout(async () => {
      try {
        if (!diagramRef.current) return
        const { toPng } = await import('html-to-image')
        const dataUrl = await toPng(diagramRef.current, {
          quality: 0.95,
          backgroundColor: isDark ? '#0f172a' : '#f8fafc',
        })
        if (dataUrl && dataUrl.length > 3000 && onSnapshot) {
          onSnapshot(dataUrl)
        }
      } catch (err) {
        // Soft fallback
      }
    }, 700)
    return () => clearTimeout(timer)
  }, [graph, isDark, showEndpoints, showPorts, simulationMode, onSnapshot])

  // ── Compute React Flow nodes and edges with hierarchical Packet Tracer layout ──
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!graph || !graph.nodes) return { initialNodes: [], initialEdges: [] }

    // Filter endpoints if toggled off
    const rawNodes = showEndpoints
      ? graph.nodes
      : graph.nodes.filter((n) => n.layer !== 'endpoint')

    const nodeIds = new Set(rawNodes.map((n) => n.id))
    const rawEdges = (graph.edges || []).filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
    )

    // Group nodes by hierarchical tier
    const byLayer = {
      edge: [],
      core: [],
      distribution: [],
      access: [],
      endpoint: [],
    }

    rawNodes.forEach((n) => {
      const layer = n.layer || 'access'
      if (!byLayer[layer]) byLayer[layer] = []
      byLayer[layer].push(n)
    })

    const LAYER_Y = {
      edge: 60,
      core: 220,
      distribution: 380,
      access: 540,
      endpoint: 700,
    }

    // Determine max items in any layer for responsive centering
    const maxItems = Math.max(
      1,
      ...Object.values(byLayer).map((items) => items.length)
    )
    const canvasWidth = Math.max(1000, maxItems * 200)

    const flowNodes = []

    Object.keys(LAYER_Y).forEach((layer) => {
      const items = byLayer[layer] || []
      const y = LAYER_Y[layer]
      const total = items.length

      items.forEach((item, idx) => {
        // Compute evenly spaced, symmetrical horizontal position
        const x = (canvasWidth / (total + 1)) * (idx + 1) - 75

        flowNodes.push({
          id: item.id,
          type: 'ciscoDevice',
          position: { x, y },
          data: {
            raw: item,
            showPorts,
            isDark,
          },
        })
      })
    })

    // Compute Packet Tracer Styled Edges
    const flowEdges = rawEdges.map((e) => {
      const isFiber = e.type === 'fiber' || e.speed === '10G' || e.speed === '40G'
      const isSerial = e.speed?.includes('M') && e.source === 'internet'

      // Packet Tracer Cabling Colors
      // Fiber: Vibrant Orange/Gold (#f97316 / #ea580c)
      // Copper: Dark Slate / Charcoal (#334155 / #94a3b8)
      // Serial: Crimson Red (#ef4444)
      const strokeColor = isSerial
        ? '#ef4444'
        : isFiber
          ? '#ea580c'
          : isDark
            ? '#94a3b8'
            : '#334155'

      const labelParts = []
      if (showPorts && (e.source_port || e.target_port)) {
        labelParts.push(`${e.source_port || ''} ➔ ${e.target_port || ''}`)
      }
      if (showSpeeds && e.label) {
        labelParts.push(e.label)
      }

      return {
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: simulationMode || isFiber,
        label: labelParts.length > 0 ? labelParts.join(' | ') : undefined,
        style: {
          stroke: strokeColor,
          strokeWidth: isFiber ? 2.5 : 2,
          strokeDasharray: isFiber ? '6 4' : undefined,
        },
        labelStyle: {
          fontSize: 9,
          fontWeight: 700,
          fill: isDark ? '#e2e8f0' : '#1e293b',
          fontFamily: 'monospace',
        },
        labelBgStyle: {
          fill: isDark ? '#0f172a' : '#ffffff',
          fillOpacity: 0.9,
          rx: 4,
          ry: 4,
          stroke: isDark ? '#334155' : '#e2e8f0',
          strokeWidth: 1,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 10,
          height: 10,
          color: strokeColor,
        },
      }
    })

    return { initialNodes: flowNodes, initialEdges: flowEdges }
  }, [graph, showEndpoints, showPorts, showSpeeds, isDark, simulationMode])

  const [nodes, setNodes] = useState(initialNodes)
  const [edges, setEdges] = useState(initialEdges)

  // Sync state when props or filters change
  React.useEffect(() => {
    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [initialNodes, initialEdges])

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )
  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  )

  const handleExportPng = async () => {
    if (!diagramRef.current) return
    try {
      const { toPng } = await import('html-to-image')
      const dataUrl = await toPng(diagramRef.current, {
        quality: 0.95,
        backgroundColor: isDark ? '#0f172a' : '#f8fafc',
      })
      if (dataUrl && onSnapshot) {
        onSnapshot(dataUrl)
      }
      const link = document.createElement('a')
      link.download = `cisco-topology-${topologyName || 'enterprise'}.png`
      link.href = dataUrl
      link.click()
    } catch (err) {
      console.error('Failed to export PNG:', err)
    }
  }

  return (
    <div className="space-y-4">
      {/* ── Authentic Cisco Packet Tracer Toolbar ── */}
      <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Left: Topology & Simulation Status */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              Topology:
            </span>
            <span className="font-bold text-brand-700 bg-brand-50 border border-brand-200 px-2.5 py-1 rounded-md uppercase text-xs">
              {topologyName?.replace('_', ' ')}
            </span>
          </div>

          {/* Packet Tracer Realtime / Simulation Pill */}
          <button
            type="button"
            onClick={() => setSimulationMode(!simulationMode)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold transition border ${simulationMode
                ? 'bg-amber-100 text-amber-800 border-amber-300 shadow-sm'
                : 'bg-emerald-50 text-emerald-700 border-emerald-300'
              }`}
            title="Toggle between Realtime Mode and Simulation Mode"
          >
            <span
              className={`w-2 h-2 rounded-full ${simulationMode ? 'bg-amber-500 animate-ping' : 'bg-emerald-500'
                }`}
            />
            {simulationMode ? 'Simulation Mode' : 'Realtime Mode'}
          </button>
        </div>

        {/* Center: Cable Legend */}
        <div className="hidden lg:flex items-center gap-4 text-[11px] font-semibold text-slate-600">
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-slate-800 inline-block" /> Copper Straight-Through
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-amber-500 border-b border-dashed border-amber-600 inline-block" /> Fiber 10G/40G
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-rose-600 inline-block" /> Serial WAN
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Link Up
          </span>
        </div>

        {/* Right: View Toggles & Actions */}
        <div className="flex items-center gap-2">
          {/* Toggle Endpoints */}
          <button
            type="button"
            onClick={() => setShowEndpoints(!showEndpoints)}
            className={`px-2.5 py-1 rounded-lg border font-semibold text-xs transition ${showEndpoints
                ? 'bg-brand-50 text-brand-700 border-brand-300'
                : 'bg-slate-100 text-slate-500 border-slate-200'
              }`}
            title="Toggle PC & Server Endpoints"
          >
            💻 Endpoints: {showEndpoints ? 'ON' : 'OFF'}
          </button>

          {/* Toggle Interface Port Labels */}
          <button
            type="button"
            onClick={() => setShowPorts(!showPorts)}
            className={`px-2.5 py-1 rounded-lg border font-semibold text-xs transition ${showPorts
                ? 'bg-brand-50 text-brand-700 border-brand-300'
                : 'bg-slate-100 text-slate-500 border-slate-200'
              }`}
            title="Toggle Interface Port Designators (Gi0/1, Te1/1/1)"
          >
            🏷️ Ports
          </button>

          {/* Theme: Packet Tracer Light vs NOC Dark */}
          <button
            type="button"
            onClick={() => setIsDark(!isDark)}
            className="px-2.5 py-1 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 font-semibold text-xs transition flex items-center gap-1"
            title="Switch between Packet Tracer Canvas and NOC Dark Console"
          >
            {isDark ? '☀️ PT Canvas' : '🌙 NOC Dark'}
          </button>

          {/* Export PNG */}
          <button
            type="button"
            onClick={handleExportPng}
            className="bg-brand-600 hover:bg-brand-700 text-white font-bold px-3 py-1 rounded-lg shadow-sm transition text-xs flex items-center gap-1"
            title="Download high-resolution topology screenshot"
          >
            📸 Export PNG
          </button>
        </div>
      </div>

      {/* ── Packet Tracer Canvas (React Flow) ── */}
      <div
        ref={diagramRef}
        id="cisco-topology-canvas"
        className={`border rounded-2xl overflow-hidden h-[620px] relative shadow-inner transition-colors duration-200 ${isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50/70 border-slate-200'
          }`}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => setSelectedNode(node.data?.raw || node)}
          fitView
          fitViewOptions={{ padding: 0.18 }}
          minZoom={0.2}
          maxZoom={1.8}
        >
          {/* Packet Tracer Dot Grid Background */}
          <Background
            color={isDark ? '#334155' : '#cbd5e1'}
            gap={24}
            size={1.5}
            variant="dots"
          />

          <Controls
            className={`shadow rounded-xl border ${isDark ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-200 text-slate-800'
              }`}
          />

          <MiniMap
            nodeColor={(n) => {
              const t = n.data?.raw?.type
              if (t === 'core' || t === 'server_switch') return '#6366f1'
              if (t === 'firewall') return '#ef4444'
              if (t === 'router' || t === 'internet') return '#0284c7'
              if (t === 'access' || t === 'distribution') return '#10b981'
              if (t === 'server') return '#f59e0b'
              return '#94a3b8'
            }}
            maskColor={isDark ? 'rgba(15, 23, 42, 0.7)' : 'rgba(241, 245, 249, 0.7)'}
            className={`rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}
          />
        </ReactFlow>
      </div>

      {/* ── Packet Tracer Device Inspector Window ── */}
      {selectedNode && (
        <PacketTracerInspector
          node={selectedNode}
          subnets={subnets}
          vlans={vlans}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  )
}
