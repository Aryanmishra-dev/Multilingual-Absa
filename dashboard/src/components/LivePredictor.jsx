import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import { Loader2 } from 'lucide-react'

const getSentimentColor = (sentiment) => {
  switch(sentiment.toLowerCase()) {
    case 'positive': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-green-200 dark:border-green-800'
    case 'negative': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-red-200 dark:border-red-800'
    case 'neutral': return 'bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-gray-200 border-gray-200 dark:border-slate-600'
    case 'conflict': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 border-orange-200 dark:border-orange-800'
    default: return 'bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-gray-200'
  }
}

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

  const renderHighlightedText = (originalText, aspects) => {
    if (!aspects || aspects.length === 0) return <p className="text-gray-700 dark:text-gray-300">{originalText}</p>
    
    // Sort aspects by start position
    const sortedAspects = [...aspects].sort((a, b) => a.start - b.start)
    
    let lastIndex = 0
    const parts = []
    
    sortedAspects.forEach((asp, i) => {
      // Add text before aspect
      if (asp.start > lastIndex) {
        parts.push(<span key={`text-${i}`}>{originalText.substring(lastIndex, asp.start)}</span>)
      }
      
      // Add aspect
      const colorClass = getSentimentColor(asp.sentiment)
      parts.push(
        <span key={`asp-${i}`} className={`px-1 rounded font-medium border ${colorClass}`}>
          {originalText.substring(asp.start, asp.end + 1)}
        </span>
      )
      
      lastIndex = asp.end + 1
    })
    
    // Add remaining text
    if (lastIndex < originalText.length) {
      parts.push(<span key="text-end">{originalText.substring(lastIndex)}</span>)
    }
    
    return <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{parts}</p>
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Left Panel: Input */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 flex flex-col h-full">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Analyze Review</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Language
          </label>
          <select 
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full rounded-md border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Auto-detect</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="hinglish">Hinglish</option>
          </select>
        </div>
        
        <div className="flex-1 flex flex-col mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Review Text
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={512}
            placeholder="Type a product review here..."
            className="flex-1 w-full rounded-md border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-900 dark:text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none min-h-[200px]"
          />
          <div className="flex justify-end mt-1">
            <span className={`text-xs ${text.length >= 512 ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}>
              {text.length} / 512
            </span>
          </div>
        </div>
        
        <button
          onClick={handlePredict}
          disabled={mutation.isPending || !text.trim()}
          className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
              Analyzing...
            </>
          ) : (
            'Analyze'
          )}
        </button>
      </div>

      {/* Right Panel: Results */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 flex flex-col h-full">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Results</h2>
        
        {!mutation.data && !mutation.isPending && (
          <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
            Enter a review and click analyze to see results.
          </div>
        )}
        
        {mutation.isPending && (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 gap-4">
            <Loader2 className="animate-spin h-8 w-8 text-indigo-500" />
            <p>Processing text via ONNX models...</p>
          </div>
        )}
        
        {mutation.data && (
          <div className="flex flex-col h-full overflow-hidden">
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">Detected Language:</span>
                <span className="px-2 py-1 bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-200 rounded text-xs font-semibold uppercase">
                  {mutation.data.detected_language}
                </span>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {mutation.data.processing_time_ms?.toFixed(1)} ms
              </div>
            </div>
            
            <div className="mb-6 bg-gray-50 dark:bg-slate-900/50 p-4 rounded-lg">
              {renderHighlightedText(mutation.data.text, mutation.data.aspects)}
            </div>
            
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Extracted Aspects</h3>
            
            <div className="flex-1 overflow-y-auto pr-2 space-y-3">
              {mutation.data.aspects && mutation.data.aspects.length > 0 ? (
                mutation.data.aspects.map((asp, idx) => (
                  <div key={idx} className="bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg p-3 shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-gray-900 dark:text-white">{asp.aspect}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase border ${getSentimentColor(asp.sentiment)}`}>
                        {asp.sentiment}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>Confidence</span>
                      <div className="flex-1 h-1.5 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-indigo-500 rounded-full" 
                          style={{ width: `${Math.round(asp.confidence * 100)}%` }}
                        ></div>
                      </div>
                      <span>{Math.round(asp.confidence * 100)}%</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-dashed border-gray-300 dark:border-slate-600">
                  No specific aspects detected
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
