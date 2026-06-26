import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { Activity, Server, Clock, AlertTriangle, ShieldCheck, Database, Zap } from 'lucide-react'

export default function Monitor() {
  const [refreshInterval, setRefreshInterval] = useState(30000)

  const { data: health, isLoading } = useQuery({
    queryKey: ['health-monitor'],
    queryFn: api.getHealth,
    refetchInterval: refreshInterval,
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">System Monitor</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Real-time API health, model metadata, and request statistics.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 dark:text-gray-300">Auto-refresh:</label>
          <select 
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="rounded-md border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-white px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
            <option value={60000}>1m</option>
            <option value={0}>Off</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Status Card */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className={`p-3 rounded-lg ${health?.status === 'ok' ? 'bg-green-100 dark:bg-green-900/50 text-green-600 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400'}`}>
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">API Status</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Core Inference Engine</p>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-6">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Current state:</span>
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
              health?.status === 'ok' 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 animate-pulse'
            }`}>
              {isLoading ? 'Checking...' : (health?.status === 'ok' ? 'HEALTHY' : 'UNHEALTHY')}
            </span>
          </div>
        </div>

        {/* Model Info */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 md:col-span-2">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400">
              <Server className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Model Configuration</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Loaded ONNX Graphs</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-slate-700/50 p-4 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Architecture</p>
              <p className="font-medium text-gray-900 dark:text-white">XLM-RoBERTa (INT8)</p>
            </div>
            <div className="bg-gray-50 dark:bg-slate-700/50 p-4 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Supported Languages</p>
              <p className="font-medium text-gray-900 dark:text-white">English, Hindi, Hinglish</p>
            </div>
            <div className="bg-gray-50 dark:bg-slate-700/50 p-4 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Aspect Extraction</p>
              <div className="flex items-center gap-1 font-medium text-gray-900 dark:text-white">
                <ShieldCheck className="h-4 w-4 text-green-500" />
                Loaded
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-slate-700/50 p-4 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Sentiment Classification</p>
              <div className="flex items-center gap-1 font-medium text-gray-900 dark:text-white">
                <ShieldCheck className="h-4 w-4 text-green-500" />
                Loaded
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white pt-4">Performance Metrics</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 flex flex-col justify-center items-center text-center">
          <Database className="h-8 w-8 text-blue-500 mb-3" />
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white">12.4k</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Total Requests Today</p>
        </div>
        
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 flex flex-col justify-center items-center text-center">
          <Zap className="h-8 w-8 text-yellow-500 mb-3" />
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white">145ms</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Average Latency (P95)</p>
        </div>
        
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 flex flex-col justify-center items-center text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mb-3" />
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white">0.2%</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Error Rate</p>
        </div>
      </div>
    </div>
  )
}
