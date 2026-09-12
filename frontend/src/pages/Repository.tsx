import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitBranch, Search, Upload, ExternalLink, GraduationCap, Sparkles, BookOpen } from 'lucide-react'
import RepoTree from '../components/RepoTree'
import { getRepository, getRepoStats } from '../lib/api'
import type { RepositoryResponse, RepoInstitution } from '../lib/types'

export default function Repository() {
  const [data, setData] = useState<RepositoryResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [stats, setStats] = useState({ subjects: 0, institutions: 0, papers: 0 })

  useEffect(() => {
    // 1. Fetch tree from backend
    getRepository()
      .then(res => {
        setData(res)
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false))

    // 2. Fetch public repo stats
    getRepoStats().then(setStats)
  }, [])

  // Filter institutions/courses/subjects based on search query
  const filteredInstitutions = (data?.institutions || []).map(inst => {
    if (!searchQuery.trim()) return inst

    const query = searchQuery.toLowerCase()
    const instMatches = inst.name.toLowerCase().includes(query)

    const filteredCourses = inst.courses.map(course => {
      const courseMatches = course.name.toLowerCase().includes(query)
      const matchingSubjects = course.subjects.filter(s =>
        s.name.toLowerCase().includes(query) || courseMatches || instMatches
      )
      return { ...course, subjects: matchingSubjects }
    }).filter(c => c.subjects.length > 0 || c.name.toLowerCase().includes(query))

    return { ...inst, courses: filteredCourses }
  }).filter(inst => inst.courses.length > 0 || inst.name.toLowerCase().includes(searchQuery.toLowerCase()))

  const totalSubs = data?.total_subjects || stats.subjects || 0
  const totalInsts = data?.total_institutions || stats.institutions || 0
  const totalPapers = data?.total_papers || stats.papers || 0

  return (
    <div className="pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-navy-100 pb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-navy-50 text-navy text-xs font-semibold mb-2">
            <GitBranch size={13} className="text-gold" /> Open Academic Precedent Archive
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-navy">
            Institutional Exam Knowledge Base
          </h1>
          <p className="text-sm text-navy-600 mt-1 max-w-xl">
            A decentralized, student-built archive. Every syllabus analyzed is preserved as structured markdown patterns and mock papers for future cohorts.
          </p>
        </div>

        <Link
          to="/upload"
          className="btn-primary text-xs sm:text-sm py-3 px-5 flex items-center gap-2 flex-shrink-0"
        >
          <Upload size={15} /> Contribute New Subject
        </Link>
      </div>

      {/* Stats Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <p className="text-xs text-navy-400 font-semibold uppercase">Participating Colleges</p>
          <p className="font-display text-2xl sm:text-3xl font-bold text-navy mt-1">
            {totalInsts}
          </p>
        </div>

        <div className="card p-4 text-center">
          <p className="text-xs text-navy-400 font-semibold uppercase">Analyzed Subjects</p>
          <p className="font-display text-2xl sm:text-3xl font-bold text-gold mt-1">
            {totalSubs}
          </p>
        </div>

        <div className="card p-4 text-center">
          <p className="text-xs text-navy-400 font-semibold uppercase">Exam Papers Archived</p>
          <p className="font-display text-2xl sm:text-3xl font-bold text-navy mt-1">
            {totalPapers}
          </p>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search size={18} className="absolute left-4 top-3.5 text-navy-400" />
        <input
          type="text"
          placeholder="Search by university name, degree (B.Tech), or subject (e.g. DBMS, Operating Systems)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-11 pr-4 py-3 bg-white border border-navy-200 rounded-2xl text-sm font-medium text-navy placeholder:text-navy-300 focus:outline-none focus:border-navy shadow-card"
        />
      </div>

      {/* Interactive Tree View */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-navy-400 px-1">
          <span>Hierarchy: Institution → Degree Program → Subject Repository</span>
          <span>Pulled live from GitHub REST API</span>
        </div>

        <RepoTree
          institutions={filteredInstitutions}
          loading={loading}
        />
      </div>
    </div>
  )
}
