import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import {
  Calendar, Clock, CheckCircle, Circle, Target, Sparkles,
  ArrowLeft, ArrowRight, RotateCcw, Award, CheckSquare, Zap
} from 'lucide-react'
import { createRevisionPlan } from '../lib/api'
import type { PlannerResponse, DayPlan, TopicItem } from '../lib/types'

export default function RevisionPlanner() {
  const { subjectId } = useParams<{ subjectId: string }>()

  // Optimization Parameters
  const [daysAvailable, setDaysAvailable] = useState<number>(7)
  const [hoursPerDay, setHoursPerDay] = useState<number>(4.0)

  // Plan State
  const [plan, setPlan] = useState<PlannerResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [recalculating, setRecalculating] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Checked items state (topic identifier -> boolean)
  const [checkedItems, setCheckedItems] = useState<{ [key: string]: boolean }>({})

  // Load completed topics from localStorage
  useEffect(() => {
    if (!subjectId) return
    const saved = localStorage.getItem(`precedent_revised_${subjectId}`)
    if (saved) {
      try {
        setCheckedItems(JSON.parse(saved))
      } catch (e) {
        console.error(e)
      }
    }
  }, [subjectId])

  // Save completed topics to localStorage
  const toggleTopic = (topicName: string) => {
    setCheckedItems(prev => {
      const next = { ...prev, [topicName]: !prev[topicName] }
      if (subjectId) {
        localStorage.setItem(`precedent_revised_${subjectId}`, JSON.stringify(next))
      }
      return next
    })
  }

  // Fetch plan
  const fetchPlan = async (days: number, hours: number) => {
    if (!subjectId) return
    setError(null)
    setRecalculating(true)

    try {
      // First check if cached in session storage from initial upload pipeline
      const cached = sessionStorage.getItem(`precedent_result_${subjectId}`)
      if (cached && days === 7 && hours === 4.0) {
        const parsed = JSON.parse(cached)
        if (parsed.plan) {
          setPlan(parsed.plan)
          setLoading(false)
          setRecalculating(false)
          return
        }
      }

      const res = await createRevisionPlan(subjectId, days, hours)
      setPlan(res)
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || err.message || 'Failed to generate knapsack revision plan.')
    } finally {
      setLoading(false)
      setRecalculating(false)
    }
  }

  useEffect(() => {
    fetchPlan(daysAvailable, hoursPerDay)
  }, [subjectId])

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault()
    fetchPlan(daysAvailable, hoursPerDay)
  }

  const coveragePercent = Math.round((plan?.expected_marks_coverage || 0) * 100)

  // Total topics in plan
  const allPlanTopics = plan?.days.flatMap(d => d.topics) || []
  const completedCount = allPlanTopics.filter(t => checkedItems[t.name]).length
  const progressPercent = allPlanTopics.length > 0 ? Math.round((completedCount / allPlanTopics.length) * 100) : 0

  return (
    <div className="pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      {/* Top Breadcrumb & Title */}
      <div>
        <Link
          to={`/dashboard/${subjectId}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-navy-500 hover:text-navy mb-2"
        >
          <ArrowLeft size={14} /> Back to Pattern Matrix
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl sm:text-4xl font-bold text-navy">
              Knapsack-Optimized Revision Timeline
            </h1>
            <p className="text-sm text-navy-600 mt-1">
              Mathematically programmed study schedule maximizing expected exam marks within your exact time envelope.
            </p>
          </div>
          <Link
            to={`/papers/${subjectId}`}
            className="btn-primary text-xs py-2 px-4 inline-flex items-center gap-1.5 flex-shrink-0"
          >
            Practice Mock Papers <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* Headline Metric Card: Expected Marks Coverage */}
      <div className="bg-gradient-to-r from-navy to-navy-800 text-white rounded-3xl p-6 md:p-8 shadow-card flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 text-center md:text-left">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gold/20 text-gold text-xs font-semibold">
            <Zap size={13} /> Mathematical Optimization Active
          </div>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-white">
            Expected Marks Coverage: <span className="text-gold">{coveragePercent}%</span>
          </h2>
          <p className="text-xs text-navy-200 max-w-lg">
            By following this exact knapsack-selected schedule, you cover high-probability topics accounting for roughly {coveragePercent}% of the historical marks distribution.
          </p>
        </div>

        {/* Circular or Bar Progress Indicator */}
        <div className="bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/10 min-w-[220px] text-center">
          <p className="text-xs text-navy-200 mb-1 font-medium">Revision Checklist Progress</p>
          <p className="text-2xl font-bold font-display text-white">
            {completedCount} / {allPlanTopics.length} Topics
          </p>
          <div className="mt-3 bg-white/20 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gold h-full rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <p className="text-[11px] text-gold mt-1 font-semibold">{progressPercent}% Completed</p>
        </div>
      </div>

      {/* Controls: Days Left & Hours Per Day */}
      <form onSubmit={handleApply} className="card p-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
            <div>
              <label className="block text-xs font-semibold text-navy mb-1.5">
                Days Available Until Exam
              </label>
              <div className="relative">
                <Calendar size={16} className="absolute left-3 top-3 text-navy-400" />
                <input
                  type="number"
                  min={1}
                  max={60}
                  value={daysAvailable}
                  onChange={(e) => setDaysAvailable(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full pl-9 pr-3 py-2 rounded-xl border border-navy-200 text-sm font-semibold text-navy focus:outline-none focus:border-navy"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-navy mb-1.5">
                Daily Study Budget (Hours / Day)
              </label>
              <div className="relative">
                <Clock size={16} className="absolute left-3 top-3 text-navy-400" />
                <input
                  type="number"
                  step="0.5"
                  min={0.5}
                  max={16}
                  value={hoursPerDay}
                  onChange={(e) => setHoursPerDay(Math.max(0.5, parseFloat(e.target.value) || 0.5))}
                  className="w-full pl-9 pr-3 py-2 rounded-xl border border-navy-200 text-sm font-semibold text-navy focus:outline-none focus:border-navy"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={recalculating}
            className="btn-primary text-xs py-2.5 px-6 flex items-center justify-center gap-2 flex-shrink-0"
          >
            <RotateCcw size={14} className={recalculating ? 'animate-spin' : ''} />
            <span>Re-solve Knapsack Schedule</span>
          </button>
        </div>
      </form>

      {/* Error Notice */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
          {error}
        </div>
      )}

      {/* Day-by-Day Timeline / Checklist */}
      {loading ? (
        <div className="p-16 text-center text-navy-400">
          <div className="w-10 h-10 border-4 border-navy-200 border-t-navy rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium">Computing marks optimization schedule...</p>
        </div>
      ) : !plan || plan.days.length === 0 ? (
        <div className="card text-center p-12">
          <p className="text-navy-500 text-sm">No topics available for schedule generation.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <h2 className="font-display text-xl font-bold text-navy">
            Optimized Daily Agenda
          </h2>

          <div className="space-y-4">
            {plan.days.map((dayPlan, dayIdx) => {
              const isDayComplete = dayPlan.topics.length > 0 && dayPlan.topics.every(t => checkedItems[t.name])

              return (
                <div
                  key={dayPlan.day}
                  className={`card transition-all duration-300 border ${
                    isDayComplete ? 'border-green-300 bg-green-50/20' : 'border-navy-100'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-navy-50 pb-3 mb-4">
                    <div className="flex items-center gap-2.5">
                      <span className={`w-8 h-8 rounded-xl font-bold text-sm flex items-center justify-center ${
                        isDayComplete ? 'bg-green-600 text-white' : 'bg-navy text-gold'
                      }`}>
                        D{dayPlan.day}
                      </span>
                      <div>
                        <h3 className="font-display text-base font-bold text-navy">
                          Day {dayPlan.day} Revision Goals
                        </h3>
                        <p className="text-xs text-navy-400">
                          Allocated: {dayPlan.total_hours} Hours Target
                        </p>
                      </div>
                    </div>

                    {isDayComplete && (
                      <span className="flex items-center gap-1 text-xs font-semibold text-green-700 bg-green-100 px-2.5 py-1 rounded-full">
                        <CheckCircle size={13} /> Day Complete
                      </span>
                    )}
                  </div>

                  {dayPlan.topics.length === 0 ? (
                    <div className="p-4 rounded-xl bg-offwhite/50 text-xs text-navy-500 text-center italic">
                      Buffer Day / Comprehensive Full Mock Test Review
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {dayPlan.topics.map((topic) => {
                        const isChecked = !!checkedItems[topic.name]

                        return (
                          <div
                            key={topic.name}
                            onClick={() => toggleTopic(topic.name)}
                            className={`p-3.5 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between gap-3 ${
                              isChecked
                                ? 'bg-navy-50/40 border-navy-100 opacity-60'
                                : 'bg-white border-navy-100 hover:border-gold hover:shadow-xs'
                            }`}
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <motion.div
                                whileTap={{ scale: 0.85 }}
                                className="flex-shrink-0"
                              >
                                {isChecked ? (
                                  <CheckCircle size={20} className="text-green-600" />
                                ) : (
                                  <Circle size={20} className="text-navy-300 hover:text-navy" />
                                )}
                              </motion.div>

                              <div className="min-w-0">
                                <p className={`text-sm font-semibold text-navy transition-all duration-200 truncate ${
                                  isChecked ? 'line-through text-navy-400' : ''
                                }`}>
                                  {topic.name}
                                </p>
                                <p className="text-xs text-navy-400 mt-0.5">
                                  Historical repeat: {Math.round(topic.frequency_score * 100)}% • Marks weight: {Math.round(topic.marks_weight * 100)}%
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-2 flex-shrink-0">
                              <span className="text-xs font-medium text-navy-600 bg-navy-50 px-2.5 py-1 rounded-lg">
                                {topic.prep_time_hrs}h
                              </span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
