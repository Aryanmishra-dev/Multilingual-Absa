import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Predict from './pages/Predict'
import Analytics from './pages/Analytics'
import Monitor from './pages/Monitor'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/predict" replace />} />
          <Route path="predict" element={<Predict />} />
          <Route path="batch" element={<Analytics />} />
          <Route path="monitor" element={<Monitor />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
