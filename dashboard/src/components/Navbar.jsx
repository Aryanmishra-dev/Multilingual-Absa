import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Brain, Moon, Sun, Menu, X, Activity } from 'lucide-react'
import { api } from '../api/client'
import { useQuery } from '@tanstack/react-query'

export default function Navbar({ toggleMobileMenu, isMobileMenuOpen }) {
  const location = useLocation()
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem('theme') === 'dark' ||
    (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
  )

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [darkMode])

  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  })

  const isHealthy = healthData?.status === 'ok'

  const navLinks = [
    { path: '/predict', label: 'Live Predict' },
    { path: '/analytics', label: 'Batch Analytics' },
    { path: '/monitor', label: 'Monitor' }
  ]

  return (
    <nav className="bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="flex items-center gap-2">
                <Brain className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                <span className="text-xl font-bold text-gray-900 dark:text-white">SentimentAI</span>
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname === link.path
                      ? 'border-indigo-500 text-gray-900 dark:text-white'
                      : 'border-transparent text-gray-500 dark:text-gray-300 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-100'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-slate-700">
              <div className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`}></div>
              <span className="text-xs font-medium text-gray-700 dark:text-gray-200">
                API {isHealthy ? 'Online' : 'Offline'}
              </span>
            </div>
            
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-slate-700 transition-colors"
            >
              {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            
            <div className="flex items-center sm:hidden">
              <button
                onClick={toggleMobileMenu}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-700"
              >
                {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {isMobileMenuOpen && (
        <div className="sm:hidden border-t border-gray-200 dark:border-slate-700">
          <div className="pt-2 pb-3 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                  location.pathname === link.path
                    ? 'bg-indigo-50 dark:bg-indigo-900/50 border-indigo-500 text-indigo-700 dark:text-indigo-200'
                    : 'border-transparent text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 hover:border-gray-300 hover:text-gray-700'
                }`}
                onClick={toggleMobileMenu}
              >
                {link.label}
              </Link>
            ))}
            <div className="pl-3 pr-4 py-2 flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`}></div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                API {isHealthy ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
