import React from 'react'
import LivePredictor from '../components/LivePredictor'

export default function Predict() {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Live Sentiment Predictor</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Enter a product review to analyze its aspects and sentiments in real-time.
        </p>
      </div>
      <div className="flex-1">
        <LivePredictor />
      </div>
    </div>
  )
}
