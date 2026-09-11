import React from 'react'
import { BookOpen, GitBranch, Shield, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-navy text-white mt-24 border-t border-navy-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gold rounded-lg flex items-center justify-center">
                <BookOpen size={16} className="text-navy" />
              </div>
              <span className="font-display font-semibold text-white text-xl tracking-tight">
                Precedent
              </span>
            </div>
            <p className="text-sm text-navy-200 max-w-sm leading-relaxed">
              "Your exam has a history. We read it."
            </p>
            <p className="text-xs text-navy-300">
              Transforming historical question papers into syllabus-mapped pattern predictions, 
              knapsack marks-optimization schedules, and reproducible public academic assets.
            </p>
          </div>

          <div>
            <h4 className="text-xs uppercase tracking-wider text-gold font-bold mb-3">Platform</h4>
            <ul className="space-y-2 text-sm text-navy-200">
              <li>
                <Link to="/upload" className="hover:text-white transition-colors">Start Analysis</Link>
              </li>
              <li>
                <Link to="/repository" className="hover:text-white transition-colors">Academic Repository</Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs uppercase tracking-wider text-gold font-bold mb-3">Hackathon</h4>
            <ul className="space-y-2 text-sm text-navy-200">
              <li className="flex items-center gap-1.5">
                <Sparkles size={14} className="text-gold" /> Horizon 2026 Round 1
              </li>
              <li className="flex items-center gap-1.5">
                <Shield size={14} className="text-gold" /> Theme: AI in Education
              </li>
              <li className="flex items-center gap-1.5">
                <GitBranch size={14} className="text-gold" /> Open Knowledge Publishing
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-navy-700 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-navy-300">
          <p>© {new Date().getFullYear()} Precedent. Engineered for high-stakes academic preparation.</p>
          <div className="flex items-center gap-4">
            <span>CPU-Inference Optimized</span>
            <span>•</span>
            <span>Zero Hallucination Anchor</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
