import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowRight, FileCheck, Layers, GitBranch, Target, BookOpen, Clock, ChevronRight, BarChart3, CalendarCheck } from 'lucide-react'
import { getRepoStats } from '../lib/api'
import Footer from '../components/Footer'

export default function Landing() {
  const [stats, setStats] = useState({ subjects: 0, institutions: 0 })

  useEffect(() => {
    getRepoStats().then(setStats)
  }, [])

  return (
    <div className="pt-16 overflow-hidden">
      {/* Hero Section */}
      <section className="relative px-4 sm:px-6 lg:px-8 pt-16 pb-24 md:pt-24 md:pb-32 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-navy-50 border border-navy-100 text-xs font-semibold text-navy mb-6 shadow-xs"
          >
            <span className="w-2 h-2 rounded-full bg-gold animate-pulse" />
            Horizon 2026 Round 1 MVP • AI in Higher Education
          </motion.div>

          {/* Main Title */}
          <motion.h1
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-navy tracking-tight leading-[1.15]"
          >
            Your exam has a history.{' '}
            <span className="italic text-gold block sm:inline">We read it.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-6 text-base sm:text-lg text-navy-600 max-w-2xl mx-auto leading-relaxed"
          >
            Precedent matches your university syllabus against multi-year Previous Year Question papers (PYQs), predicts high-yield topics, builds a marks-optimized study schedule, and auto-publishes assets to an open repository for future students.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              to="/upload"
              className="w-full sm:w-auto btn-primary text-base flex items-center justify-center gap-2 py-3.5 px-8 shadow-card"
            >
              Analyze Your Exam Pattern <ArrowRight size={18} />
            </Link>
            <Link
              to="/repository"
              className="w-full sm:w-auto btn-outline text-base flex items-center justify-center gap-2 py-3.5 px-6"
            >
              <GitBranch size={18} /> Browse Public Repository
            </Link>
          </motion.div>

          {/* Live Repository Counter */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-12 inline-flex items-center gap-6 px-6 py-3 rounded-2xl bg-white border border-navy-100 shadow-card text-xs text-navy-600"
          >
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="font-semibold text-navy">{stats.subjects}</span> Subjects Analyzed
            </div>
            <div className="h-4 w-[1px] bg-navy-100" />
            <div className="flex items-center gap-2">
              <span className="font-semibold text-navy">{stats.institutions}</span> Partner Institutions
            </div>
          </motion.div>
        </div>

        {/* Animated Visual Flow: PYQs In -> Prediction + Plan Out */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-16 md:mt-20 max-w-5xl mx-auto"
        >
          <div className="bg-white rounded-3xl border border-navy-100 shadow-card p-6 md:p-10 relative overflow-hidden">
            <div className="text-center mb-8">
              <p className="text-xs uppercase tracking-widest text-gold font-bold">End-to-End Pipeline</p>
              <h2 className="font-display text-2xl font-bold text-navy mt-1">
                How Precedent Turns Raw Papers into Rank
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
              {/* Step 1 */}
              <div className="p-5 rounded-2xl bg-offwhite/80 border border-navy-100 space-y-3">
                <div className="w-10 h-10 rounded-xl bg-navy text-gold flex items-center justify-center font-bold">
                  01
                </div>
                <h3 className="font-display text-base font-bold text-navy">
                  Multi-Year Ingestion
                </h3>
                <p className="text-xs text-navy-600 leading-relaxed">
                  Upload official syllabus and raw PYQ PDFs. PyMuPDF extracts questions, marks distributions, and section weights into normalized vectors.
                </p>
                <div className="pt-2 flex flex-wrap gap-1.5 text-[11px] font-mono text-navy-500">
                  <span className="bg-white px-2 py-0.5 rounded border border-navy-100">Syllabus PDF</span>
                  <span className="bg-white px-2 py-0.5 rounded border border-navy-100">5-Year PYQs</span>
                </div>
              </div>

              {/* Step 2 */}
              <div className="p-5 rounded-2xl bg-offwhite/80 border border-gold-300 relative shadow-xs space-y-3">
                <div className="w-10 h-10 rounded-xl bg-gold text-navy flex items-center justify-center font-bold">
                  02
                </div>
                <h3 className="font-display text-base font-bold text-navy">
                  Semantic Clustering
                </h3>
                <p className="text-xs text-navy-600 leading-relaxed">
                  MiniLM sentence transformers project questions into dense vector space, clustering rephrased prompts across exam cycles to discover true repeat frequencies.
                </p>
                <div className="pt-2 flex items-center gap-1 text-[11px] font-semibold text-gold-700">
                  <BarChart3 size={13} /> Cosine Similarity Clustering
                </div>
              </div>

              {/* Step 3 */}
              <div className="p-5 rounded-2xl bg-offwhite/80 border border-navy-100 space-y-3">
                <div className="w-10 h-10 rounded-xl bg-navy-800 text-white flex items-center justify-center font-bold">
                  03
                </div>
                <h3 className="font-display text-base font-bold text-navy">
                  Knapsack Plan & GitHub
                </h3>
                <p className="text-xs text-navy-600 leading-relaxed">
                  Custom knapsack solver computes maximum expected marks given remaining days and hours. Simultaneously auto-publishes datasets to GitHub.
                </p>
                <div className="pt-2 flex items-center gap-1 text-[11px] font-semibold text-navy-600">
                  <CalendarCheck size={13} /> Marks-Budget Optimization
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Feature Deep Dive */}
      <section className="bg-white border-t border-navy-100 py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs uppercase tracking-widest text-gold font-bold">Core Differentiators</span>
            <h2 className="font-display text-3xl md:text-4xl font-bold text-navy mt-2">
              Why Precedent Outperforms Generic Study Tools
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="card space-y-3">
              <div className="w-10 h-10 bg-navy-50 text-navy rounded-xl flex items-center justify-center">
                <Target size={20} />
              </div>
              <h3 className="font-display text-lg font-bold text-navy">
                Pattern Repeat Rate
              </h3>
              <p className="text-xs text-navy-600 leading-relaxed">
                Computes genuine historical appearance metrics (e.g., "70% repeat across 5 sessions") rather than subjective guessing.
              </p>
            </div>

            <div className="card space-y-3">
              <div className="w-10 h-10 bg-gold-50 text-gold-600 rounded-xl flex items-center justify-center">
                <Clock size={20} />
              </div>
              <h3 className="font-display text-lg font-bold text-navy">
                Knapsack Time Optimizer
              </h3>
              <p className="text-xs text-navy-600 leading-relaxed">
                Allocate your 12 or 48 remaining preparation hours mathematically to maximize marks yield per revision minute.
              </p>
            </div>

            <div className="card space-y-3">
              <div className="w-10 h-10 bg-navy-50 text-navy rounded-xl flex items-center justify-center">
                <BookOpen size={20} />
              </div>
              <h3 className="font-display text-lg font-bold text-navy">
                Realistic Simulated Mocks
              </h3>
              <p className="text-xs text-navy-600 leading-relaxed">
                Infers Section layout, compulsory rules, and marks allocation to produce downloadable printable mock papers.
              </p>
            </div>

            <div className="card space-y-3">
              <div className="w-10 h-10 bg-gold-50 text-gold-600 rounded-xl flex items-center justify-center">
                <GitBranch size={20} />
              </div>
              <h3 className="font-display text-lg font-bold text-navy">
                Institutional Knowledge Base
              </h3>
              <p className="text-xs text-navy-600 leading-relaxed">
                Every analysis automatically pushes organized subject folders to a public GitHub repo for upcoming academic batches.
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
