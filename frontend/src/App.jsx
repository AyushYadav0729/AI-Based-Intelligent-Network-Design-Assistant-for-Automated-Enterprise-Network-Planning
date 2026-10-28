import React from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import WizardPage from './pages/WizardPage'
import ProjectsPage from './pages/ProjectsPage'
import HealthBadge from './components/HealthBadge'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Top nav ─────────────────────────────────────────────────── */}
      <header className="bg-brand-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🌐</span>
            <span className="text-xl font-bold tracking-tight">
              AI Network Design Assistant
            </span>
          </div>
          <nav className="flex items-center gap-6 text-sm font-medium">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                isActive ? 'underline underline-offset-4' : 'opacity-75 hover:opacity-100'
              }
            >
              New Design
            </NavLink>
            <NavLink
              to="/projects"
              className={({ isActive }) =>
                isActive ? 'underline underline-offset-4' : 'opacity-75 hover:opacity-100'
              }
            >
              My Projects
            </NavLink>
            <HealthBadge />
          </nav>
        </div>
      </header>

      {/* ── Page content ────────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/" element={<WizardPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
        </Routes>
      </main>

      <footer className="text-center text-xs text-gray-400 py-3 border-t">
        AI Network Design Assistant · Phase 1 skeleton
      </footer>
    </div>
  )
}
