import React, { useState } from 'react'
import RequirementsForm from '../components/RequirementsForm'
import ReviewStep from '../components/ReviewStep'
import TopologyDiagram from '../components/TopologyDiagram'
import IpVlanTable from '../components/IpVlanTable'
import DevicesCostTable from '../components/DevicesCostTable'
import SecurityPanel from '../components/SecurityPanel'
import ValidationPanel from '../components/ValidationPanel'
import ComparePanel from '../components/ComparePanel'
import DecisionExplainer from '../components/DecisionExplainer'
import ExportPanel from '../components/ExportPanel'
import { generateDesign, saveProject } from '../api/client'
import { SAMPLE_SCENARIOS } from '../utils/sampleScenarios'

const DEFAULT_REQUIREMENTS = SAMPLE_SCENARIOS.small_office.data

export default function WizardPage() {
  const [step, setStep] = useState(1) // 1 = form, 2 = review, 3 = results
  const [requirements, setRequirements] = useState(DEFAULT_REQUIREMENTS)
  const [isGenerating, setIsGenerating] = useState(false)
  const [designResponse, setDesignResponse] = useState(null)
  const [activeVariant, setActiveVariant] = useState('balanced') // 'budget', 'balanced', 'high_performance'
  const [activeTab, setActiveTab] = useState('topology') // 'topology', 'ipvlan', 'devices', 'security', 'validation', 'compare'
  const [savedSuccess, setSavedSuccess] = useState(false)
  const [errorNotice, setErrorNotice] = useState(null)
  const [diagramSnapshot, setDiagramSnapshot] = useState(null)

  const handleGenerate = async () => {
    setIsGenerating(true)
    setErrorNotice(null)
    try {
      const res = await generateDesign(requirements)
      setDesignResponse(res.data)
      setActiveVariant('balanced')
      setActiveTab('topology')
      setStep(3)
    } catch (err) {
      setErrorNotice(err.response?.data?.detail || err.message || 'Failed to generate design')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSaveProject = async () => {
    if (!designResponse) return
    try {
      await saveProject({
        name: requirements.org_name,
        requirements,
        results: designResponse,
        explanation_source: designResponse.explanation_source || 'template',
      })
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 3000)
    } catch (err) {
      alert('Failed to save project: ' + (err.response?.data?.detail || err.message))
    }
  }

  const currentResult = designResponse?.variants?.[activeVariant]

  return (
    <div className="space-y-6">
      {/* ── Wizard Step Indicator ── */}
      <div className="flex items-center justify-between bg-white border p-3 rounded-xl shadow-sm text-xs">
        <div className="flex items-center gap-6">
          <button
            type="button"
            onClick={() => setStep(1)}
            className={`flex items-center gap-2 font-semibold transition ${
              step === 1 ? 'text-brand-700 font-bold' : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
              step === 1 ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}>1</span>
            Requirements Form
          </button>

          <span className="text-gray-300">/</span>

          <button
            type="button"
            onClick={() => setStep(2)}
            className={`flex items-center gap-2 font-semibold transition ${
              step === 2 ? 'text-brand-700 font-bold' : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
              step === 2 ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}>2</span>
            Review & Sizing
          </button>

          <span className="text-gray-300">/</span>

          <button
            type="button"
            onClick={() => designResponse && setStep(3)}
            disabled={!designResponse}
            className={`flex items-center gap-2 font-semibold transition ${
              step === 3 ? 'text-brand-700 font-bold' : 'text-gray-400 disabled:opacity-40'
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
              step === 3 ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}>3</span>
            Design Results & Variants
          </button>
        </div>

        {step === 3 && (
          <div className="flex items-center gap-3">
            {savedSuccess && (
              <span className="text-emerald-700 font-bold text-xs animate-in fade-in">
                ✓ Project Saved to Database!
              </span>
            )}
            <button
              type="button"
              onClick={handleSaveProject}
              className="bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg shadow-sm transition flex items-center gap-1.5"
            >
              💾 Save Project
            </button>
            <button
              type="button"
              onClick={() => setStep(1)}
              className="border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold text-xs px-3 py-1.5 rounded-lg transition"
            >
              + New Design
            </button>
          </div>
        )}
      </div>

      {errorNotice && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-xl flex items-center justify-between">
          <span>⚠ {errorNotice}</span>
          <button onClick={() => setErrorNotice(null)} className="font-bold">✕</button>
        </div>
      )}

      {/* ── Step Views ── */}
      {step === 1 && (
        <RequirementsForm
          values={requirements}
          onChange={setRequirements}
          onNext={() => setStep(2)}
        />
      )}

      {step === 2 && (
        <ReviewStep
          values={requirements}
          onBack={() => setStep(1)}
          onGenerate={handleGenerate}
          isGenerating={isGenerating}
        />
      )}

      {step === 3 && currentResult && (
        <div className="space-y-6">
          {/* ── Variant Switcher Header ── */}
          <div className="bg-white border rounded-xl shadow-sm p-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase">Selected Architecture Tier:</span>
              <div className="text-lg font-bold text-gray-900 mt-0.5 capitalize flex items-center gap-2">
                {activeVariant.replace('_', ' ')} Tier
                <span className="text-xs font-normal text-gray-500">
                  (${currentResult.cost?.total_cost?.toLocaleString(undefined, { minimumFractionDigits: 2 })})
                </span>
              </div>
            </div>

            <div className="flex bg-gray-100 p-1 rounded-xl text-xs font-semibold">
              <button
                type="button"
                onClick={() => setActiveVariant('budget')}
                className={`px-3.5 py-1.5 rounded-lg transition ${
                  activeVariant === 'budget' ? 'bg-white shadow text-emerald-800 font-bold' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Budget Tier
              </button>
              <button
                type="button"
                onClick={() => setActiveVariant('balanced')}
                className={`px-3.5 py-1.5 rounded-lg transition ${
                  activeVariant === 'balanced' ? 'bg-white shadow text-brand-800 font-bold' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Balanced (Recommended)
              </button>
              <button
                type="button"
                onClick={() => setActiveVariant('high_performance')}
                className={`px-3.5 py-1.5 rounded-lg transition ${
                  activeVariant === 'high_performance' ? 'bg-white shadow text-indigo-800 font-bold' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                High-Performance
              </button>
            </div>
          </div>

          {/* ── Tabs Navigation ── */}
          <div className="border-b border-gray-200 flex flex-wrap gap-2 text-xs font-bold">
            {[
              { id: 'topology', label: '1. Topology Diagram' },
              { id: 'ipvlan', label: '2. IP & VLAN Plan' },
              { id: 'devices', label: '3. Devices & Cost' },
              { id: 'security', label: '4. Security & ACLs' },
              { id: 'validation', label: `5. Validation (${currentResult.validation?.length || 0})` },
              { id: 'compare', label: '6. Compare All 3 Variants' },
              { id: 'export', label: '7. Export & Save' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`py-2.5 px-4 rounded-t-lg transition border-b-2 ${
                  activeTab === tab.id
                    ? 'border-brand-600 text-brand-700 bg-white shadow-sm'
                    : 'border-transparent text-gray-500 hover:text-gray-800'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* ── Tab Content ── */}
          {/* ── Topology Tab ── */}
          <div
            id="topology-diagram-container"
            style={{
              display: activeTab === 'topology' ? 'block' : 'none',
            }}
          >
            <TopologyDiagram
              graph={currentResult.graph}
              topologyName={currentResult.topology}
              vlans={currentResult.vlans}
              subnets={currentResult.subnets}
              devices={currentResult.devices}
              routing={currentResult.routing}
              onSnapshot={setDiagramSnapshot}
            />
          </div>

          {activeTab === 'ipvlan' && (
            <IpVlanTable
              vlans={currentResult.vlans}
              subnets={currentResult.subnets}
              p2pLinks={currentResult.p2p_links}
              capacity={currentResult.capacity}
            />
          )}

          {activeTab === 'devices' && (
            <DevicesCostTable
              devices={currentResult.devices}
              cost={currentResult.cost}
            />
          )}

          {activeTab === 'security' && (
            <SecurityPanel security={currentResult.security} />
          )}

          {activeTab === 'validation' && (
            <ValidationPanel validation={currentResult.validation} />
          )}

          {activeTab === 'compare' && (
            <ComparePanel
              comparison={designResponse.comparison}
              summary={designResponse.comparison_summary}
              onSelectVariant={setActiveVariant}
              activeVariant={activeVariant}
            />
          )}

          {activeTab === 'export' && (
            <ExportPanel
              design={currentResult}
              requirements={requirements}
              designResponse={designResponse}
              activeVariant={activeVariant}
              onSaveProject={handleSaveProject}
              savedSuccess={savedSuccess}
              diagramSnapshot={diagramSnapshot}
            />
          )}

          {/* ── Decision Explainer Drawer / Accordion ── */}
          <DecisionExplainer
            decisions={currentResult.decisions}
            source={designResponse.explanation_source}
          />
        </div>
      )}
    </div>
  )
}
