import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const NAV = [
  { path: '/predict',   icon: 'psychology',    label: 'Predictor' },
  { path: '/batch',     icon: 'cloud_upload',  label: 'Batch Analytics' },
  { path: '/monitor',   icon: 'monitoring',    label: 'System Health' },
]

function MSIcon({ name, filled = false, size = 20, className = '' }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={{
        fontSize: size,
        fontVariationSettings: filled ? `'FILL' 1, 'wght' 400` : `'FILL' 0, 'wght' 300`,
      }}
    >
      {name}
    </span>
  )
}

export { MSIcon }

export default function Sidebar({ isOpen, onClose }) {
  const location = useLocation()

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  })
  const isHealthy = health?.status === 'ok'

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <nav
        aria-label="Main navigation"
        className={`
          fixed left-0 top-0 h-screen w-64 z-50 flex flex-col
          bg-surface-container border-r border-white/[0.07]
          transition-transform duration-250 ease-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-xl py-xl">
          <MSIcon name="psychology" filled size={28} className="text-primary" />
          <div>
            <h1 className="text-title-lg font-semibold text-primary leading-tight">SentimentAI</h1>
            <p className="font-mono text-label-sm text-on-surface-variant">Analysis Engine v2.4</p>
          </div>
        </div>

        {/* CTA */}
        <div className="px-xl mb-xl">
          <Link
            to="/predict"
            onClick={onClose}
            className="btn-primary w-full text-sm"
          >
            <MSIcon name="add" size={18} />
            New Analysis
          </Link>
        </div>

        {/* Nav links */}
        <ul className="flex-1 px-sm space-y-0.5 overflow-y-auto">
          {NAV.map(({ path, icon, label }) => {
            const active = location.pathname === path
            return (
              <li key={path}>
                <Link
                  to={path}
                  onClick={onClose}
                  className={active ? 'nav-item-active' : 'nav-item'}
                  aria-current={active ? 'page' : undefined}
                >
                  <MSIcon name={icon} filled={active} size={20} />
                  <span>{label}</span>
                </Link>
              </li>
            )
          })}
        </ul>

        {/* Bottom section */}
        <div className="px-sm pt-sm pb-xl border-t border-white/[0.06] space-y-0.5 mt-auto">
          {/* API health pill */}
          <div className="flex items-center gap-2 px-3 py-2 mb-1">
            <span
              className={`w-2 h-2 rounded-full flex-shrink-0 ${
                isHealthy ? 'bg-tertiary shadow-glow-positive' : 'bg-error shadow-glow-negative animate-pulse'
              }`}
            />
            <span className="font-mono text-label-md text-on-surface-variant">
              API {isHealthy ? 'Online' : 'Offline'}
            </span>
          </div>

          <Link to="/monitor" onClick={onClose} className="nav-item">
            <MSIcon name="settings" size={20} />
            <span>Settings</span>
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-item"
          >
            <MSIcon name="menu_book" size={20} />
            <span>API Docs</span>
          </a>
        </div>
      </nav>
    </>
  )
}
