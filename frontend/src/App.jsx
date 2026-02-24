import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import NeuroTutor from './pages/StudentView'
import ProfessorDashboard from './pages/ProfessorDashboard'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<NeuroTutor />} />
      <Route path="/professor" element={<ProfessorDashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
