import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import LogDetail from './pages/LogDetail'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Tiffin Times - Emergency Call Logs</h1>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/log/:id" element={<LogDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App