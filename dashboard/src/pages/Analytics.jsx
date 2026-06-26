import React, { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { UploadCloud, File, AlertCircle, Loader2, Download } from 'lucide-react'
import toast from 'react-hot-toast'
import SentimentChart from '../components/SentimentChart'
import AspectHeatmap from '../components/AspectHeatmap'
import LanguagePie from '../components/LanguagePie'

export default function Analytics() {
  const [file, setFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [isPolling, setIsPolling] = useState(false)

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: (f) => api.uploadBatch(f),
    onSuccess: (data) => {
      setJobId(data.job_id)
      setIsPolling(true)
      toast.success("Batch job queued successfully")
    }
  })

  // Poll Job Status
  const { data: jobStatus } = useQuery({
    queryKey: ['batchStatus', jobId],
    queryFn: () => api.getBatchStatus(jobId),
    enabled: isPolling && !!jobId,
    refetchInterval: isPolling ? 2000 : false,
  })

  useEffect(() => {
    if (jobStatus?.status === 'completed' || jobStatus?.status === 'failed') {
      setIsPolling(false)
      if (jobStatus.status === 'completed') {
        toast.success("Batch processing completed!")
      } else {
        toast.error("Batch processing failed")
      }
    }
  }, [jobStatus])

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles?.length > 0) {
      const selectedFile = acceptedFiles[0]
      if (!selectedFile.name.endsWith('.csv')) {
        toast.error("Please upload a CSV file")
        return
      }
      setFile(selectedFile)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1
  })

  const handleUpload = () => {
    if (!file) return
    uploadMutation.mutate(file)
  }

  const resetUpload = () => {
    setFile(null)
    setJobId(null)
    setIsPolling(false)
  }

  const progress = jobStatus ? Math.min(100, Math.round((jobStatus.processed / jobStatus.total_reviews) * 100)) : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Batch Analytics</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Upload a CSV of reviews for bulk aspect-based sentiment analysis.
        </p>
      </div>

      {/* Upload Section */}
      {!jobId && (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-8">
          <div 
            {...getRootProps()} 
            className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
              isDragActive 
                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' 
                : 'border-gray-300 dark:border-slate-600 hover:border-indigo-400 hover:bg-gray-50 dark:hover:bg-slate-700/50'
            }`}
          >
            <input {...getInputProps()} />
            <UploadCloud className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {isDragActive ? "Drop the CSV file here" : "Drag & drop a CSV file, or click to select"}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Must contain a 'text' column. Maximum 10,000 rows.
            </p>
          </div>

          {file && (
            <div className="mt-6 flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-700 rounded-lg border border-gray-200 dark:border-slate-600">
              <div className="flex items-center gap-3">
                <File className="h-6 w-6 text-indigo-500" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{file.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <div className="flex gap-3">
                <button 
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  className="px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-md hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                >
                  Remove
                </button>
                <button 
                  onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                  disabled={uploadMutation.isPending}
                  className="px-4 py-1.5 flex items-center text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {uploadMutation.isPending ? <Loader2 className="animate-spin h-4 w-4 mr-2" /> : null}
                  Process File
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Progress Section */}
      {jobId && (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center gap-2">
                {jobStatus?.status === 'completed' && <span className="h-3 w-3 rounded-full bg-green-500"></span>}
                {jobStatus?.status === 'processing' && <span className="h-3 w-3 rounded-full bg-blue-500 animate-pulse"></span>}
                {jobStatus?.status === 'failed' && <span className="h-3 w-3 rounded-full bg-red-500"></span>}
                {jobStatus?.status === 'queued' && <span className="h-3 w-3 rounded-full bg-gray-400"></span>}
                Job Status: <span className="capitalize">{jobStatus?.status || 'Queued'}</span>
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">ID: {jobId}</p>
            </div>
            
            {jobStatus?.status === 'completed' && (
              <div className="flex gap-3">
                <button
                  onClick={resetUpload}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-md hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                >
                  Upload New
                </button>
                {jobStatus?.result_url && (
                  <a 
                    href={`http://localhost:8000${jobStatus.result_url}`} 
                    download
                    className="flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Results CSV
                  </a>
                )}
              </div>
            )}
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm font-medium text-gray-700 dark:text-gray-300">
              <span>Progress</span>
              <span>{jobStatus ? `${jobStatus.processed} / ${jobStatus.total_reviews} (${progress}%)` : '0%'}</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2.5 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ease-out ${
                  jobStatus?.status === 'failed' ? 'bg-red-500' : 'bg-indigo-600'
                }`}
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}

      {/* Analytics Charts */}
      {jobStatus?.status === 'completed' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            <AspectHeatmap />
          </div>
          <div>
            <LanguagePie />
          </div>
          <div className="lg:col-span-2 xl:col-span-3">
            <SentimentChart />
          </div>
        </div>
      )}
    </div>
  )
}
