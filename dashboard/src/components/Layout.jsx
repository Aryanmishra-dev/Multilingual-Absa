import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

export default function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors duration-200 flex flex-col">
      <Navbar 
        isMobileMenuOpen={isMobileMenuOpen} 
        toggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)} 
      />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500 dark:text-gray-400">
          SentimentAI — Phase 6 Analytics Dashboard
        </div>
      </footer>
    </div>
  )
}
