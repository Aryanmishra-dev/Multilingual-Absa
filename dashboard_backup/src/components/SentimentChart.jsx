import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function SentimentChart({ data }) {
  // Mock data if none provided (for initial dev)
  const chartData = data || [
    { name: 'Jan', positive: 400, negative: 240, neutral: 100, conflict: 50 },
    { name: 'Feb', positive: 300, negative: 139, neutral: 200, conflict: 40 },
    { name: 'Mar', positive: 200, negative: 980, neutral: 150, conflict: 100 },
    { name: 'Apr', positive: 278, negative: 390, neutral: 250, conflict: 60 },
    { name: 'May', positive: 189, negative: 480, neutral: 180, conflict: 70 },
    { name: 'Jun', positive: 239, negative: 380, neutral: 210, conflict: 80 },
    { name: 'Jul', positive: 349, negative: 430, neutral: 230, conflict: 90 },
  ]

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 h-96">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Sentiment Over Time</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
          <XAxis dataKey="name" stroke="#6B7280" fontSize={12} />
          <YAxis stroke="#6B7280" fontSize={12} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F9FAFB' }}
            itemStyle={{ color: '#F9FAFB' }}
          />
          <Legend />
          <Line type="monotone" dataKey="positive" stroke="#10B981" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
          <Line type="monotone" dataKey="negative" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="neutral" stroke="#6B7280" strokeWidth={2} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="conflict" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
