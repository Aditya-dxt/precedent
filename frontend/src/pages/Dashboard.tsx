import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell
} from 'recharts'
import {
  ArrowRight, Calendar, FileText, GitBranch, CheckCircle2,
  Share2, Award, Flame, ExternalLink, Sparkles, Loader2
} from 'lucide-react'
import confetti from 'canvas-confetti'
import TopicCard from '../components/TopicCard'
import { publishToGitHub } from '../lib/api'
import type { TopicItem, AnalysisResult } from '../lib/types'

export default function Dashboard() {
  const { subjectId } = useParams<{ subjectId: string }>()

  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [topics, setTopics] = useState<TopicItem[]>([])
  const [loading, setLoading] = useState(true)

  // Publishing state
  const [publishing, setPublishing] = useState(false)
  const [publishSuccess, setPublishSuccess] = useState<string | null>(null)
  const [publishError, setPublishError] = useState<string | null>(null)

  useEffect(() => {
    if (!subjectId) return

    // 1. Try retrieving from sessionStorage first (from direct upload flow)
    const cached = sessionStorage.getItem(`precedent_result_${subjectId}`)
    if (cached) {
      try {
        const parsed: AnalysisResult = JSON.parse(cached)
        setResult(parsed)
        setTopics(parsed.topics || [])
        setLoading(false)
        return
      } catch (e) {
        console.error(e)
      }
    }

    // 2. Fetch from backend /api/topics/:subjectId
    fetch(`/api/topics/${subjectId}`)
      .then(r => r.json())
      .then(data => {
        if (data && data.topics) {
          setTopics(data.topics)
        }
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [subjectId])

  const handlePublish = async () => {
    if (!subjectId) return
    setPublishing(true)
    setPublishError(null)

    try {
      const resp = await publishToGitHub(subjectId)
      if (resp.success) {
        setPublishSuccess(resp.github_url)
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#1B2A4A', '#C9922A', '#F5F3EF']
        })
      } else {
        throw new Error('Failed to commit to repository.')
      }
    } catch (err: any) {
      console.error(err)
      setPublishError(err?.response?.data?.detail || err.message || 'GitHub publishing requires GITHUB_TOKEN configured on the backend.')
    } finally {
      setPublishing(false)
    }
  }

  // Prepare data for horizontal bar chart
  const chartData = topics.slice(0, 8).map(t => ({
    name: t.name.length > 22 ? t.name.substring(0, 20) + '...' : t.name,
    frequency: Math.round(t.frequency_score * 100),
    marksWeight: Math.round(t.marks_weight * 100),
  }))

  const totalYears = result?.total_years || (topics[0]?.appeared_in_years?.length ? Math.max(...topics.flatMap(t => t.appeared_in_years)) - Math.min(...topics.flatMap(t => t.appeared_in_years)) + 1 : 0)

  return (
    <div className="pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-navy-100 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge-high flex items-center gap-1">
              <Flame size={12} /> Pattern Predictions Live
            </span>
            <span className="text-xs text-navy-400">
              Subject ID: {subjectId?.substring(0, 8)}...
            </span>
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-navy mt-1">
            Exam Pattern & High-Yield Topic Matrix
          </h1>
          <p className="text-sm text-navy-600 mt-1">
            Clustered across authentic historical question papers and mapped directly to syllabus competencies.
          </p>
        </div>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center gap-3">
          <Link
            to={`/planner/${subjectId}`}
            className="btn-gold text-xs sm:text-sm py-2.5 px-4 flex items-center gap-1.5 font-semibold"
          >
            <Calendar size={16} /> Open Revision Planner
          </Link>
          <Link
            to={`/papers/${subjectId}`}
            className="btn-primary text-xs sm:text-sm py-2.5 px-4 flex items-center gap-1.5"
          >
            <FileText size={16} /> View Mock Papers
          </Link>
        </div>
      </div>

      {/* GitHub Auto-Publish Banner */}
      <div className="bg-white rounded-2xl border border-navy-100 p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-navy-50 text-navy flex items-center justify-center flex-shrink-0 mt-0.5">
            <GitBranch size={20} />
          </div>
          <div>
            <h3 className="font-display text-base font-bold text-navy">
              Contribute to Precedent Institutional Knowledge Repository
            </h3>
            <p className="text-xs text-navy-500 mt-0.5">
              Publish these analyzed topics, parsed papers, and mock papers as a structured markdown artifact to GitHub.
            </p>
          </div>
        </div>

        <div>
          {publishSuccess ? (
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex items-center gap-3"
            >
              <div className="flex items-center gap-1.5 text-xs font-semibold text-green-700 bg-green-50 px-3 py-2 rounded-xl border border-green-200">
                <CheckCircle2 size={16} className="text-green-600" />
                Published to Precedent Repository ✓
              </div>
              <a
                href={publishSuccess}
                target="_blank"
                rel="noreferrer"
                className="btn-primary text-xs py-2 px-3 flex items-center gap-1"
              >
                View on GitHub <ExternalLink size={13} />
              </a>
            </motion.div>
          ) : (
            <div className="flex flex-col items-end gap-1">
              <button
                onClick={handlePublish}
                disabled={publishing}
                className="btn-primary text-xs py-2.5 px-5 flex items-center gap-2 disabled:opacity-50"
              >
                {publishing ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Committing via GitHub API...</span>
                  </>
                ) : (
                  <>
                    <Share2 size={14} />
                    <span>Auto-Publish to GitHub</span>
                  </>
                )}
              </button>
              {publishError && (
                <span className="text-[11px] text-red-600 max-w-xs text-right">
                  {publishError}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="p-16 text-center text-navy-400">
          <div className="w-10 h-10 border-4 border-navy-200 border-t-navy rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium">Loading pattern analysis data...</p>
        </div>
      ) : topics.length === 0 ? (
        <div className="card text-center p-12 space-y-3">
          <Award size={36} className="mx-auto text-navy-300" />
          <h3 className="font-display text-lg font-bold text-navy">No Topic Predictions Found</h3>
          <p className="text-xs text-navy-500 max-w-md mx-auto">
            We could not extract any matching topics from the uploaded files. Please ensure you uploaded an official syllabus and PYQs with readable text.
          </p>
          <Link to="/upload" className="btn-primary text-xs inline-block py-2 px-5 mt-2">
            Upload New Subject
          </Link>
        </div>
      ) : (
        <>
          {/* Visual Chart: Top High-Probability Topics */}
          <div className="card space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-navy-50 pb-3">
              <div>
                <h2 className="font-display text-xl font-bold text-navy">
                  High-Yield Topic Repeat Frequency
                </h2>
                <p className="text-xs text-navy-500">
                  Calculated based on semantic question recurrence across past examination cycles.
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-navy" />
                  <span className="text-navy-600 font-medium">Repeat %</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded bg-gold" />
                  <span className="text-navy-600 font-medium">Marks Weight %</span>
                </div>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 11, fill: '#1B2A4A' }} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={150}
                    tick={{ fontSize: 11, fill: '#1B2A4A' }}
                  />
                  <Tooltip
                    formatter={(val: any, name: any) => [
                      `${val}%`,
                      name === 'frequency' ? 'Historical Repeat Rate' : 'Marks Allocation Weight'
                    ]}
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: '12px',
                      border: '1px solid #C9D3E8',
                      fontSize: '12px'
                    }}
                  />
                  <Bar dataKey="frequency" fill="#1B2A4A" radius={[0, 4, 4, 0]} barSize={12} />
                  <Bar dataKey="marksWeight" fill="#C9922A" radius={[0, 4, 4, 0]} barSize={12} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Staggered Ranked Topic Cards */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-xl font-bold text-navy">
                Complete Ranked Syllabus Breakdown ({topics.length} Topics Identified)
              </h2>
              <span className="text-xs text-navy-400">
                Sorted by composite historical yield
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topics.map((t, idx) => (
                <motion.div
                  key={t.name}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: Math.min(idx * 0.05, 0.6) }}
                >
                  <TopicCard
                    topic={t}
                    rank={idx + 1}
                    totalYears={totalYears}
                  />
                </motion.div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
