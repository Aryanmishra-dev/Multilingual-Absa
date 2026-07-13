import React from 'react'
import LivePredictor from '../components/LivePredictor'

export default function Predict() {
  return (
    <div className="space-y-xl">
      <div>
        <h1 className="text-headline-md text-on-surface">Live Sentiment Predictor</h1>
        <p className="mt-1 text-body-md text-on-surface-variant max-w-2xl">
          Enter text to analyze its aspects and sentiments in real-time.
          The model automatically identifies the language and extracts key phrases.
        </p>
      </div>
      <LivePredictor />
    </div>
  )
}
