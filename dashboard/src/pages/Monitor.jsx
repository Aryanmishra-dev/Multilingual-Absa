import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { MSIcon } from '../components/Sidebar'

// ── Stat card with sparkline area ─────────────────────────────────────────────
function StatCard({ icon, label, value, sub, sparkColor, positive }) {
  return (
    <div className="stat-card group">
      {/* Sparkline BG */}
      <div
        className="absolute bottom-0 left-0 w-full h-16 opacity-40 group-hover:opacity-70 transition-opacity pointer-events-none"
        style={{
          background: `linear-gradient(180deg, ${sparkColor}33 0%, transparent 100%)`,
        }}
      >
        <svg viewBox="0 0 100 40" className="w-full h-full" preserveAspectRatio="none">
          <path
            d={positive
              ? "M0 40 L0 28 Q25 24 50 20 T100 14 L100 40 Z"
              : "M0 40 L0 32 Q25 30 50 26 T100 22 L100 40 Z"}
            fill={`${sparkColor}22`}
            stroke={sparkColor}
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-lg">
          <span className="material-symbols-outlined text-2xl" style={{ color: sparkColor, fontVariationSettings: `'FILL' 1` }}>
            {icon}
          </span>
          <span className="font-mono text-label-md text-on-surface-variant uppercase tracking-wider">{label}</span>
        </div>
        <p className="text-display text-on-surface font-semibold">{value}</p>
        {sub && <p className="font-mono text-label-sm text-on-surface-variant mt-1">{sub}</p>}
      </div>
    </div>
  )
}

// ── Health status chip ────────────────────────────────────────────────────────
function HealthChip({ ok }) {
  return ok ? (
    <span className="badge-positive">
      <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse-slow flex-shrink-0" />
      Healthy
    </span>
  ) : (
    <span className="badge-error">
      <span className="w-2 h-2 rounded-full bg-error animate-pulse flex-shrink-0" />
      Degraded
    </span>
  )
}

// ── Info row ─────────────────────────────────────────────────────────────────
function InfoRow({ label, value, valueClass = '' }) {
  return (
    <div className="bg-surface rounded-lg p-md">
      <p className="font-mono text-label-sm text-on-surface-variant mb-1">{label}</p>
      <p className={`text-body-md text-on-surface font-medium ${valueClass}`}>{value}</p>
    </div>
  )
}

function LoadedBadge() {
  return (
    <div className="flex items-center gap-1.5 text-body-md text-on-surface font-medium">
      <MSIcon name="check_circle" size={16} className="text-tertiary" />
      Loaded
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Monitor() {
  const [refreshInterval, setRefreshInterval] = useState(30000)

  const { data: health, isLoading } = useQuery({
    queryKey: ['health-monitor'],
    queryFn: api.getHealth,
    refetchInterval: refreshInterval || false,
  })

  const isHealthy = health?.status === 'ok'

  return (
    <div className="space-y-xl">
      {/* Page header */}
      <div className="flex flex-wrap justify-between items-end gap-4">
        <div>
          <h1 className="text-headline-md text-on-surface">System Monitor</h1>
          <p className="mt-1 text-body-md text-on-surface-variant">
            Real-time API health, model metadata, and request statistics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="refresh-select" className="font-mono text-label-sm text-on-surface-variant">
            Auto-refresh
          </label>
          <select
            id="refresh-select"
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="input-base py-1 text-body-sm"
          >
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
            <option value={60000}>1m</option>
            <option value={0}>Off</option>
          </select>
        </div>
      </div>

      {/* ── Health + Model config ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-xl">
        {/* API Status */}
        <div className="lg:col-span-4 card flex flex-col gap-lg">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${isHealthy ? 'bg-tertiary/10' : 'bg-error/10'}`}>
              <MSIcon
                name="monitor_heart"
                size={24}
                className={isHealthy ? 'text-tertiary' : 'text-error'}
              />
            </div>
            <div>
              <h2 className="text-title-lg text-on-surface">API Status</h2>
              <p className="font-mono text-label-sm text-on-surface-variant">Core Inference Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-lg border-t border-white/[0.06]">
            <span className="text-body-md text-on-surface-variant">Current state:</span>
            {isLoading ? (
              <span className="badge-neutral animate-pulse">Checking…</span>
            ) : (
              <HealthChip ok={isHealthy} />
            )}
          </div>
        </div>

        {/* Model Configuration */}
        <div className="lg:col-span-8 card">
          <div className="flex items-center gap-3 mb-xl">
            <div className="p-2.5 rounded-lg bg-primary/10">
              <MSIcon name="memory" size={24} className="text-primary" />
            </div>
            <div>
              <h2 className="text-title-lg text-on-surface">Model Configuration</h2>
              <p className="font-mono text-label-sm text-on-surface-variant">Loaded ONNX Graphs</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-md">
            <InfoRow label="Architecture"           value="XLM-RoBERTa (INT8)" />
            <InfoRow label="Supported Languages"    value="English, Hindi, Hinglish" />
            <div className="bg-surface rounded-lg p-md">
              <p className="font-mono text-label-sm text-on-surface-variant mb-1">Aspect Extraction</p>
              <LoadedBadge />
            </div>
            <div className="bg-surface rounded-lg p-md">
              <p className="font-mono text-label-sm text-on-surface-variant mb-1">Sentiment Classification</p>
              <LoadedBadge />
            </div>
          </div>
        </div>
      </div>

      {/* ── Performance metrics ── */}
      <div>
        <h2 className="text-headline-sm text-on-surface mb-lg">Performance Metrics</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-xl">
          <StatCard
            icon="database"
            label="Total Requests Today"
            value="12.4k"
            sub="↑ 8% vs yesterday"
            sparkColor="#c0c1ff"
            positive
          />
          <StatCard
            icon="bolt"
            label="Avg Latency (P95)"
            value="145ms"
            sub="Well within SLA"
            sparkColor="#4edea3"
            positive
          />
          <StatCard
            icon="warning"
            label="Error Rate"
            value="0.2%"
            sub="Last 24 hours"
            sparkColor="#ffb4ab"
            positive={false}
          />
        </div>
      </div>

      {/* ── Recent Activity ── */}
      <div className="card">
        <h2 className="text-title-lg text-on-surface mb-lg">Recent Endpoint Activity</h2>
        <div className="space-y-2">
          {[
            { method: 'POST', path: '/predict',      status: 200, time: '3.5ms',  ago: '2s ago' },
            { method: 'GET',  path: '/health',       status: 200, time: '0.8ms',  ago: '5s ago' },
            { method: 'POST', path: '/batch',        status: 202, time: '12.1ms', ago: '1m ago' },
            { method: 'GET',  path: '/status/abc12', status: 200, time: '1.2ms',  ago: '1m ago' },
            { method: 'POST', path: '/predict',      status: 500, time: '23ms',   ago: '3m ago' },
          ].map((req, i) => (
            <div key={i} className="flex items-center gap-4 py-2 px-md rounded-lg hover:bg-white/[0.03] transition-colors">
              <span className={`font-mono text-label-sm w-10 flex-shrink-0 ${
                req.method === 'POST' ? 'text-primary' : 'text-tertiary'
              }`}>
                {req.method}
              </span>
              <span className="font-mono text-body-sm text-on-surface flex-1 truncate">{req.path}</span>
              <span className={`font-mono text-label-sm w-10 text-right flex-shrink-0 ${
                req.status >= 500 ? 'text-error' : req.status >= 400 ? 'text-warning' : 'text-tertiary'
              }`}>
                {req.status}
              </span>
              <span className="font-mono text-label-sm text-on-surface-variant w-14 text-right flex-shrink-0">{req.time}</span>
              <span className="font-mono text-label-sm text-on-surface-variant/50 w-16 text-right hidden sm:block flex-shrink-0">{req.ago}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
