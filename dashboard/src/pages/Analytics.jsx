import React, { useState, useCallback, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { MSIcon } from '../components/Sidebar'
import AspectHeatmap from '../components/AspectHeatmap'
import LanguagePie from '../components/LanguagePie'
import SentimentChart from '../components/SentimentChart'
import { API_URL } from '../config'

// ── Status badge ──────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  switch (status) {
    case 'completed':
      return (
        <span className="badge-positive">
          <span className="w-1.5 h-1.5 rounded-full bg-tertiary flex-shrink-0" />
          Completed
        </span>
      )
    case 'processing':
      return (
        <span className="badge-processing">
          <span className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
          Processing
        </span>
      )
    case 'queued':
      return (
        <span className="badge-neutral">
          <span className="w-1.5 h-1.5 rounded-full bg-outline flex-shrink-0" />
          Queued
        </span>
      )
    case 'failed':
      return (
        <span className="badge-error">
          <span className="w-1.5 h-1.5 rounded-full bg-error flex-shrink-0" />
          Failed
        </span>
      )
    default:
      return <span className="badge-neutral">{status}</span>
  }
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Analytics() {
  const [file, setFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [isPolling, setIsPolling] = useState(false)

  // Upload mutation — unchanged API call
  const uploadMutation = useMutation({
    mutationFn: (f) => api.uploadBatch(f),
    onSuccess: (data) => {
      setJobId(data.job_id)
      setIsPolling(true)
      toast.success('Batch job queued successfully')
    },
  })

  // Poll job status — unchanged API call
  const { data: jobStatus } = useQuery({
    queryKey: ['batchStatus', jobId],
    queryFn: () => api.getBatchStatus(jobId),
    enabled: isPolling && !!jobId,
    refetchInterval: isPolling ? 2000 : false,
  })

  useEffect(() => {
    if (jobStatus?.status === 'completed' || jobStatus?.status === 'failed') {
      setIsPolling(false)
      if (jobStatus.status === 'completed') toast.success('Batch processing completed!')
      else toast.error('Batch processing failed')
    }
  }, [jobStatus])

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles?.length > 0) {
      const f = acceptedFiles[0]
      if (!f.name.endsWith('.csv')) { toast.error('Please upload a CSV file'); return }
      setFile(f)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
  })

  const handleUpload = () => { if (file) uploadMutation.mutate(file) }
  const resetUpload  = () => { setFile(null); setJobId(null); setIsPolling(false) }

  const progress = jobStatus
    ? Math.min(100, Math.round((jobStatus.processed / jobStatus.total_reviews) * 100))
    : 0

  return (
    <div className="space-y-xl">
      {/* Page header */}
      <div>
        <h1 className="text-headline-md text-on-surface">Batch Analytics</h1>
        <p className="mt-1 text-body-md text-on-surface-variant">
          Upload a CSV of reviews for bulk aspect-based sentiment analysis.
        </p>
      </div>

      {/* ── Upload zone (hidden when job is active) ── */}
      {!jobId && (
        <section className="card">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-12 flex flex-col items-center
                        justify-center text-center cursor-pointer transition-colors duration-200
                        ${isDragActive
                          ? 'drag-active border-primary/60'
                          : 'border-white/[0.14] hover:border-primary/40 hover:bg-primary/[0.02]'
                        }`}
          >
            <input {...getInputProps()} />
            <MSIcon
              name="cloud_upload"
              size={48}
              className="text-on-surface-variant mb-4"
            />
            <h3 className="text-headline-sm text-on-surface mb-2">
              {isDragActive ? 'Drop the CSV here…' : 'Drag & drop a CSV, or click to select'}
            </h3>
            <p className="text-body-md text-on-surface-variant max-w-sm">
              Must contain a <code className="font-mono text-primary px-1">text</code> column.
              Maximum 10,000 rows. Files are deleted after analysis.
            </p>
          </div>

          {/* Selected file row */}
          {file && (
            <div className="mt-lg flex items-center justify-between
                            p-md rounded-lg bg-surface-container-low border border-white/[0.08]
                            animate-slide-in">
              <div className="flex items-center gap-3">
                <MSIcon name="description" size={20} className="text-primary" />
                <div>
                  <p className="text-body-md text-on-surface font-medium">{file.name}</p>
                  <p className="font-mono text-label-sm text-on-surface-variant">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null) }}
                  className="px-3 py-1.5 text-body-sm text-on-surface-variant border border-white/[0.12]
                             rounded-lg hover:bg-white/[0.05] hover:text-on-surface transition-colors"
                >
                  Remove
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleUpload() }}
                  disabled={uploadMutation.isPending}
                  className="btn-primary text-body-sm"
                >
                  {uploadMutation.isPending ? (
                    <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                  ) : (
                    <MSIcon name="rocket_launch" size={16} />
                  )}
                  Process File
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      {/* ── Job progress ── */}
      {jobId && (
        <section className="card animate-fade-in">
          <div className="flex flex-wrap justify-between items-start gap-4 mb-lg">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <StatusBadge status={jobStatus?.status || 'queued'} />
                <h3 className="text-title-lg text-on-surface">
                  {file?.name || 'Batch Job'}
                </h3>
              </div>
              <p className="font-mono text-label-sm text-on-surface-variant">ID: {jobId}</p>
            </div>
            <div className="flex gap-2">
              {jobStatus?.status === 'completed' && (
                <>
                  <button onClick={resetUpload} className="px-3 py-1.5 text-body-sm border border-white/[0.12] rounded-lg text-on-surface-variant hover:bg-white/[0.05] transition-colors">
                    Upload New
                  </button>
                  {jobStatus?.result_url && (
                    <a
                      href={`${API_URL}${jobStatus.result_url}`}
                      download
                      className="btn-primary text-body-sm"
                    >
                      <MSIcon name="download" size={16} />
                      Download CSV
                    </a>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between font-mono text-label-sm text-on-surface-variant">
              <span>Progress</span>
              <span>
                {jobStatus ? `${jobStatus.processed} / ${jobStatus.total_reviews}` : '0'} rows
                &nbsp;({progress}%)
              </span>
            </div>
            <div className="w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  jobStatus?.status === 'failed' ? 'bg-error' : 'bg-primary'
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </section>
      )}

      {/* ── Recent batches mock table ── */}
      {!jobId && (
        <section>
          <h2 className="text-headline-sm text-on-surface mb-lg">Recent Batches</h2>
          <div className="card overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.08] bg-surface-container-high/50">
                    <th className="font-mono text-label-sm text-on-surface-variant py-3 px-xl">Filename</th>
                    <th className="font-mono text-label-sm text-on-surface-variant py-3 px-lg">Rows</th>
                    <th className="font-mono text-label-sm text-on-surface-variant py-3 px-lg">Status</th>
                    <th className="font-mono text-label-sm text-on-surface-variant py-3 px-xl text-right">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {[
                    { name: 'q3_customer_feedback.csv',    rows: '4,250', status: 'completed', date: 'Today, 14:32' },
                    { name: 'product_launch_tweets.csv',   rows: '8,912', status: 'processing', date: 'Today, 14:15' },
                    { name: 'corrupted_export_09.csv',     rows: '—',     status: 'failed',     date: 'Yesterday' },
                  ].map((row, i) => (
                    <tr key={i} className="hover:bg-white/[0.03] transition-colors">
                      <td className="py-3 px-xl">
                        <div className="flex items-center gap-2 text-body-md text-on-surface">
                          <MSIcon name="description" size={16} className="text-on-surface-variant" />
                          {row.name}
                        </div>
                      </td>
                      <td className="py-3 px-lg font-mono text-body-sm text-on-surface-variant">{row.rows}</td>
                      <td className="py-3 px-lg"><StatusBadge status={row.status} /></td>
                      <td className="py-3 px-xl text-right font-mono text-body-sm text-on-surface-variant">{row.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* ── Charts (post-completion) ── */}
      {jobStatus?.status === 'completed' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-xl animate-fade-in">
          <div className="xl:col-span-2"><AspectHeatmap /></div>
          <div><LanguagePie /></div>
          <div className="lg:col-span-2 xl:col-span-3"><SentimentChart /></div>
        </div>
      )}
    </div>
  )
}
