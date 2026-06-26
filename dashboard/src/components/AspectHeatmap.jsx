import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'

export default function AspectHeatmap({ data }) {
  // Mock data if none provided
  const chartData = data || [
    { aspect: 'food', positive: 120, negative: 30, neutral: 10, conflict: 5 },
    { aspect: 'service', positive: 50, negative: 80, neutral: 20, conflict: 15 },
    { aspect: 'price', positive: 40, negative: 60, neutral: 15, conflict: 5 },
    { aspect: 'ambience', positive: 90, negative: 10, neutral: 5, conflict: 2 },
    { aspect: 'staff', positive: 60, negative: 40, neutral: 10, conflict: 8 },
  ]

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 h-96">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Top Aspects by Sentiment</h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          layout="vertical"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} horizontal={false} />
          <XAxis type="number" stroke="#6B7280" fontSize={12} />
          <YAxis dataKey="aspect" type="category" stroke="#6B7280" fontSize={12} width={80} />
          <Tooltip 
            cursor={{fill: 'rgba(107, 114, 128, 0.1)'}}
            contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F9FAFB' }}
          />
          <Legend />
          <Bar dataKey="positive" stackId="a" fill="#10B981" />
          <Bar dataKey="negative" stackId="a" fill="#EF4444" />
          <Bar dataKey="neutral" stackId="a" fill="#6B7280" />
          <Bar dataKey="conflict" stackId="a" fill="#F59E0B" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
