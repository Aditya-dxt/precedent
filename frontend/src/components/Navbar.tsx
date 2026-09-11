import { Link, useLocation } from 'react-router-dom'
import { BookOpen, GitBranch, Upload } from 'lucide-react'

export default function Navbar() {
  const location = useLocation()
  const isLanding = location.pathname === '/'

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isLanding ? 'bg-transparent' : 'bg-white/95 backdrop-blur-md border-b border-navy-100 shadow-sm'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-navy rounded-lg flex items-center justify-center">
            <BookOpen size={16} className="text-gold" />
          </div>
          <span className="font-display font-semibold text-navy text-lg tracking-tight">
            Precedent
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden sm:flex items-center gap-6">
          <Link
            to="/repository"
            className="flex items-center gap-1.5 text-sm text-navy-600 hover:text-navy font-medium transition-colors"
          >
            <GitBranch size={15} />
            Repository
          </Link>
          <Link
            to="/upload"
            className="flex items-center gap-1.5 btn-primary text-sm py-2 px-4"
          >
            <Upload size={14} />
            Start Analysis
          </Link>
        </div>

        {/* Mobile CTA */}
        <Link to="/upload" className="sm:hidden btn-primary text-sm py-2 px-3">
          Analyze
        </Link>
      </div>
    </nav>
  )
}
