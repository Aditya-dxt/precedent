import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Upload from './pages/Upload'
import Processing from './pages/Processing'
import Dashboard from './pages/Dashboard'
import RevisionPlanner from './pages/RevisionPlanner'
import MockPapers from './pages/MockPapers'
import Repository from './pages/Repository'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-offwhite font-sans">
        <Navbar />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/processing/:jobId" element={<Processing />} />
          <Route path="/dashboard/:subjectId" element={<Dashboard />} />
          <Route path="/planner/:subjectId" element={<RevisionPlanner />} />
          <Route path="/papers/:subjectId" element={<MockPapers />} />
          <Route path="/repository" element={<Repository />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
