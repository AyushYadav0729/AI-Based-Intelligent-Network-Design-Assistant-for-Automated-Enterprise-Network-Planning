import React, { useState } from 'react'

export default function DecisionExplainer({ decisions, source }) {
  const [openIds, setOpenIds] = useState({})

  const toggle = (idx) => {
    setOpenIds((prev) => ({ ...prev, [idx]: !prev[idx] }))
  }

  const items = decisions || []

  return (
    <div className="bg-white border rounded-xl shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between border-b pb-2.5">
        <div className="flex items-center gap-2">
          <span className="font-bold text-sm text-gray-800">💡 Architectural Decisions & Reasoning</span>
          <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
            {source === 'llm' ? '✨ AI Explanations' : '📄 Deterministic Rules'}
          </span>
        </div>
        <span className="text-xs text-gray-400">{items.length} decisions logged</span>
      </div>

      <div className="space-y-2">
        {items.map((dec, idx) => {
          const isOpen = !!openIds[idx]
          return (
            <div key={idx} className="border rounded-lg p-3 text-xs space-y-1.5 transition">
              <div
                className="flex items-center justify-between cursor-pointer select-none"
                onClick={() => toggle(idx)}
              >
                <div className="flex items-center gap-2">
                  <span className="font-bold uppercase text-brand-700 bg-brand-50 px-1.5 py-0.5 rounded text-[10px]">
                    {dec.stage}
                  </span>
                  <span className="font-semibold text-gray-900">{dec.choice}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-gray-400">{dec.reason_code}</span>
                  <span className="text-gray-400 font-bold text-sm">{isOpen ? '▾' : '▸'}</span>
                </div>
              </div>

              {isOpen && (
                <div className="pt-2 border-t mt-1 text-gray-600 space-y-1 bg-gray-50/50 p-2 rounded">
                  <div className="font-mono text-[10px] text-gray-500">
                    Parameters:{' '}
                    {Object.entries(dec.params || {})
                      .map(([k, v]) => `${k}=${v}`)
                      .join(' · ')}
                  </div>
                  {dec.explanation && (
                    <p className="text-gray-800 font-medium italic mt-1">"{dec.explanation}"</p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

