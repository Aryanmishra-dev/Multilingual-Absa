import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import { MSIcon } from './Sidebar'

const MAX_CHARS = 512

// ── Helpers ──────────────────────────────────────────────────────────────────

function sentimentBadgeClass(s) {
  switch (s) {
    case 'positive': return 'badge-positive'
    case 'negative': return 'badge-negative'
    case 'conflict': return 'badge-error'
    default:         return 'badge-neutral'
  }
}

function highlightClass(s) {
  switch (s) {
    case 'positive': return 'highlight-positive'
    case 'negative': return 'highlight-negative'
    case 'conflict': return 'highlight-negative'
    default:         return 'highlight-neutral'
  }
}

function confidenceBarColor(s) {
  if (s === 'positive') return 'bg-tertiary'
  if (s === 'negative' || s === 'conflict') return 'bg-error'
  return 'bg-outline'
}

function sentimentDot(s) {
  if (s === 'positive') return 'bg-tertiary'
  if (s === 'negative' || s === 'conflict') return 'bg-error'
  return 'bg-outline'
}

// Build annotated text spans from API response
function AnnotatedText({ text, aspects }) {
  if (!aspects || aspects.length === 0) {
    return <p className="text-body-md text-on-surface leading-loose">{text}</p>
  }

  const sorted = [...aspects].sort((a, b) => a.start - b.start)
  const parts = []
  let cursor = 0

  sorted.forEach((asp, i) => {
    if (asp.start > cursor) {
      parts.push(<span key={`t${i}`}>{text.slice(cursor, asp.start)}</span>)
    }
    parts.push(
      <span key={`a${i}`} className={highlightClass(asp.sentiment)} title={`${asp.sentiment} · ${Math.round(asp.confidence * 100)}%`}>
        {text.slice(asp.start, asp.end)}
      </span>
    )
    cursor = asp.end
  })

  if (cursor < text.length) parts.push(<span key="tend">{text.slice(cursor)}</span>)

  return <p className="text-body-md text-on-surface leading-loose">{parts}</p>
}

// ── Skeleton ─────────────────────────────────────────────────────────────────
function Skeleton({ className = '' }) {
  return (
    <div className={`animate-pulse bg-surface-container-high rounded ${className}`} />
  )
}

// ── Empty / Loading state for results panel ──────────────────────────────────
function ResultsEmpty() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 py-16 text-on-surface-variant">
      <span className="material-symbols-outlined text-5xl opacity-30"
        style={{ fontVariationSettings: `'FILL' 0, 'wght' 200` }}>
        psychology
      </span>
      <p className="text-body-md opacity-60">Enter a review and click Analyze to see results</p>
    </div>
  )
}

function ResultsLoading() {
  return (
    <div className="flex flex-col gap-4 animate-fade-in">
      <div className="bg-surface rounded-lg p-lg space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
      {[1, 2, 3].map(i => (
        <div key={i} className="bg-surface-container rounded-lg p-md space-y-2 border border-white/[0.06]">
          <div className="flex justify-between">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-16" />
          </div>
          <Skeleton className="h-1.5 w-full" />
        </div>
      ))}
    </div>
  )
}

// ── Aspect Card ───────────────────────────────────────────────────────────────
function AspectCard({ asp }) {
  const pct = Math.round(asp.confidence * 100)
  return (
    <div className="bg-surface-container rounded-lg p-md border border-white/[0.06] hover:border-white/[0.12] transition-colors animate-slide-in">
      <div className="flex justify-between items-center mb-2">
        <span className="text-body-md text-on-surface font-medium">{asp.aspect}</span>
        <span className={sentimentBadgeClass(asp.sentiment)}>
          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${sentimentDot(asp.sentiment)}`} />
          {asp.sentiment}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="font-mono text-label-sm text-on-surface-variant w-20">Confidence</span>
        <div className="flex-1 h-1 bg-surface rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${confidenceBarColor(asp.sentiment)}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className={`font-mono text-label-sm w-8 text-right ${
          asp.sentiment === 'positive' ? 'text-tertiary' :
          asp.sentiment === 'negative' ? 'text-error' : 'text-on-surface-variant'
        }`}>{pct}%</span>
      </div>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function LivePredictor() {
  const [text, setText] = useState('')
  const [language, setLanguage] = useState('')

  const mutation = useMutation({
    mutationFn: (data) => api.predict(data.text, data.language || null),
  })

  const handlePredict = () => {
    if (!text.trim()) return
    mutation.mutate({ text, language })
  }

  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') handlePredict()
  }

  const data = mutation.data

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-xl">
      {/* ── Left: Input ─────────────────────────────────────── */}
      <div className="lg:col-span-7 flex flex-col">
        <div className="card-low flex flex-col h-full">
          {/* Card header */}
          <div className="flex justify-between items-center mb-lg pb-md border-b border-white/[0.06]">
            <h3 className="font-mono text-label-md text-on-surface-variant uppercase tracking-wider">
              Analyze Input
            </h3>
            <div className="flex items-center gap-2">
              <label htmlFor="lang-select" className="font-mono text-label-sm text-on-surface-variant">
                Language
              </label>
              <select
                id="lang-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input-base py-1 text-body-sm"
              >
                <option value="">Auto-detect</option>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="hinglish">Hinglish</option>
              </select>
            </div>
          </div>

          {/* Textarea */}
          <div className="flex-1 flex flex-col mb-lg">
            <label htmlFor="review-text" className="font-mono text-label-sm text-on-surface-variant mb-2">
              Source Text
            </label>
            <textarea
              id="review-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={MAX_CHARS}
              placeholder="Paste your review, article, or social media post here…"
              aria-label="Review text input"
              className="input-base flex-1 min-h-[260px] resize-none leading-relaxed"
            />
            <div className="flex justify-between mt-2">
              <span className="font-mono text-label-sm text-on-surface-variant/50">
                ⌘ Enter to analyze
              </span>
              <span className={`font-mono text-label-sm ${text.length >= MAX_CHARS ? 'text-error' : 'text-on-surface-variant/50'}`}>
                {text.length} / {MAX_CHARS}
              </span>
            </div>
          </div>

          {/* Analyze button */}
          <button
            onClick={handlePredict}
            disabled={mutation.isPending || !text.trim()}
            className="btn-primary"
            aria-label="Run sentiment analysis"
          >
            {mutation.isPending ? (
              <>
                <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                Analyzing…
              </>
            ) : (
              <>
                <MSIcon name="bolt" size={16} />
                Analyze
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Right: Results ──────────────────────────────────── */}
      <div className="lg:col-span-5 flex flex-col">
        <div className="glass-panel rounded-xl flex flex-col h-full p-xl">
          {/* Card header */}
          <div className="flex justify-between items-center mb-lg pb-md border-b border-white/[0.06]">
            <h3 className="font-mono text-label-md text-on-surface-variant uppercase tracking-wider">
              Analysis Results
            </h3>
            {data && (
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1 bg-surface-container px-2 py-0.5 rounded border border-white/[0.08]">
                  <span className="font-mono text-label-sm text-on-surface-variant">LANG:</span>
                  <span className="font-mono text-label-sm text-primary uppercase">{data.detected_language}</span>
                </span>
                <span className="flex items-center gap-1 text-on-surface-variant">
                  <MSIcon name="timer" size={14} />
                  <span className="font-mono text-label-sm">{data.processing_time_ms?.toFixed(1)}ms</span>
                </span>
              </div>
            )}
          </div>

          {/* Content states */}
          {!data && !mutation.isPending && <ResultsEmpty />}
          {mutation.isPending && <ResultsLoading />}

          {data && (
            <div className="flex flex-col gap-lg flex-1 overflow-hidden animate-fade-in">
              {/* Annotated text */}
              <div className="bg-surface border border-white/[0.06] rounded-lg p-md">
                <AnnotatedText text={data.text} aspects={data.aspects} />
              </div>

              {/* Legend */}
              <div className="flex items-center gap-4 flex-wrap">
                <span className="flex items-center gap-1.5 font-mono text-label-sm text-on-surface-variant">
                  <span className="w-3 h-3 rounded highlight-positive inline-block" /> Positive
                </span>
                <span className="flex items-center gap-1.5 font-mono text-label-sm text-on-surface-variant">
                  <span className="w-3 h-3 rounded highlight-negative inline-block" /> Negative
                </span>
                <span className="flex items-center gap-1.5 font-mono text-label-sm text-on-surface-variant">
                  <span className="w-3 h-3 rounded highlight-neutral inline-block" /> Neutral
                </span>
              </div>

              {/* Aspects list */}
              <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                <h4 className="font-mono text-label-sm text-on-surface-variant uppercase tracking-wider mb-2">
                  Extracted Aspects
                </h4>
                {data.aspects && data.aspects.length > 0 ? (
                  data.aspects.map((asp, i) => <AspectCard key={i} asp={asp} />)
                ) : (
                  <div className="text-center py-8 rounded-lg border border-dashed border-white/[0.12] text-on-surface-variant text-body-sm">
                    No specific aspects detected
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
