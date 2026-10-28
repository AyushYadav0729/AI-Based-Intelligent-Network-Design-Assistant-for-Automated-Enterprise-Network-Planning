import React, { useState } from 'react'
import axios from 'axios'

export default function FreeTextBox({ onParsed }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState(null)

  const handleParse = async () => {
    if (!text.trim()) return
    setLoading(true)
    setNotice(null)

    try {
      const res = await axios.post('/api/llm/parse', { text })
      const data = res.data

      if (data.source === 'none') {
        setNotice({
          type: 'warning',
          text: data.message || 'LLM parsing unavailable. Template and manual entry remain fully functional.',
        })
      } else if (data.requirements) {
        onParsed(data.requirements)
        setNotice({
          type: 'success',
          text: '✓ Requirements extracted successfully! Please review the form below.',
        })
      }
    } catch (err) {
      setNotice({
        type: 'error',
        text: err.response?.data?.detail || err.message || 'Failed to parse natural language text',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gradient-to-r from-brand-50 via-indigo-50 to-purple-50 border border-brand-200 rounded-xl p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">✨</span>
          <span className="font-bold text-sm text-gray-900">AI Natural Language Requirements Assistant</span>
          <span className="text-[10px] font-bold bg-white text-brand-700 px-2 py-0.5 rounded-full border border-brand-200">
            Powered by Gemini
          </span>
        </div>
        <span className="text-xs text-gray-400">Describe your campus in plain English</span>
      </div>

      <div className="space-y-2">
        <textarea
          rows={3}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder='e.g. "Design a hospital network with 4 floors and about 400 staff across Emergency, Wards, Radiology, and Admin. We need 20 servers, critical patient record security, full redundancy, and 30% growth over 5 years."'
          className="w-full bg-white border border-brand-200 rounded-lg p-3 text-xs placeholder:text-gray-400 focus:ring-2 focus:ring-brand-500 outline-none"
        />

        <div className="flex items-center justify-between">
          <div className="text-xs">
            {notice && (
              <span
                className={`font-semibold ${
                  notice.type === 'success'
                    ? 'text-emerald-700'
                    : notice.type === 'warning'
                    ? 'text-amber-700'
                    : 'text-rose-700'
                }`}
              >
                {notice.text}
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={handleParse}
            disabled={loading || !text.trim()}
            className="bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs px-5 py-2 rounded-lg shadow transition flex items-center gap-1.5 disabled:opacity-40"
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Parsing Requirements...
              </>
            ) : (
              <>✨ Auto-Fill Form with AI</>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

