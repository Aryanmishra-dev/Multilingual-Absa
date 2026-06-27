import React, { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Sidebar, { MSIcon } from './Sidebar'

const PAGE_TITLES = {
  '/predict': 'Live Predictor',
  '/batch':   'Batch Analytics',
  '/monitor': 'System Monitor',
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const pageTitle = PAGE_TITLES[location.pathname] || 'SentimentAI'

  return (
    <div className="min-h-screen bg-background flex">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#222a3d',
            color: '#dae2fd',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '8px',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: '#4edea3', secondary: '#0b1326' } },
          error:   { iconTheme: { primary: '#ffb4ab', secondary: '#0b1326' } },
        }}
      />

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Right of sidebar */}
      <div className="flex-1 md:ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="fixed top-0 right-0 left-0 md:left-64 h-16 z-30
                           bg-surface/80 backdrop-blur-glass border-b border-white/[0.06]
                           flex items-center justify-between px-xl gap-4">
          {/* Mobile hamburger + brand */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 rounded-lg text-on-surface-variant hover:text-on-surface
                         hover:bg-white/[0.05] transition-colors"
              aria-label="Open navigation"
            >
              <MSIcon name="menu" size={22} />
            </button>
            <div className="md:hidden flex items-center gap-2">
              <MSIcon name="psychology" filled size={22} className="text-primary" />
              <span className="font-semibold text-on-surface">SentimentAI</span>
            </div>
            <h2 className="hidden md:block text-body-md font-medium text-on-surface-variant">
              {pageTitle}
            </h2>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            <button
              className="p-2 rounded-lg text-on-surface-variant hover:text-on-surface
                         hover:bg-white/[0.05] transition-colors"
              aria-label="Notifications"
            >
              <MSIcon name="notifications" size={20} />
            </button>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5
                         border border-white/[0.12] rounded-lg
                         font-mono text-label-md text-on-surface-variant
                         hover:text-on-surface hover:border-white/25
                         transition-colors duration-150"
            >
              <MSIcon name="api" size={14} />
              API Docs
            </a>
            {/* Avatar placeholder */}
            <div className="w-8 h-8 rounded-full bg-surface-container-highest
                            border border-white/[0.12] flex items-center justify-center
                            text-on-surface-variant text-xs font-medium select-none">
              <MSIcon name="person" size={18} />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 pt-16 overflow-y-auto">
          <div className="max-w-[1280px] mx-auto px-lg md:px-3xl py-xl md:py-2xl">
            <Outlet />
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/[0.05] py-4 text-center font-mono text-label-sm text-on-surface-variant">
          SentimentAI — Phase 6 Analytics Dashboard
        </footer>
      </div>
    </div>
  )
}
