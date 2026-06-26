import React from 'react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function LanguagePie({ data }) {
  // Mock data if none provided
  const chartData = data || [
    { name: 'English', value: 400 },
    { name: 'Hindi', value: 300 },
    { name: 'Hinglish', value: 150 },
  ]

  const COLORS = ['#3B82F6', '#F97316', '#10B981']

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 h-96">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Language Distribution</h3>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="45%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={5}
            dataKey="value"
            stroke="none"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F9FAFB' }}
            itemStyle={{ color: '#F9FAFB' }}
          />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
