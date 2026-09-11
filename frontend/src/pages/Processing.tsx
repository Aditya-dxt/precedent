import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { AlertCircle, ArrowRight, BookOpen, RefreshCw } from 'lucide-react'
import ProgressStep from '../components/ProgressStep'
import { pollStatus } from '../lib/api'
import type { StatusResponse } from '../lib/types'

const PIPELINE_STEPS = [
  { id: 'pending', label: 'Queued for Analysis', description: 'Allocating in-memory workers and checking document integrity' },
  { id: 'parsing', label: 'Parsing Official Syllabus', description: 'Deconstructing syllabus into discrete modules, units, and learning goals' },
  { id: 'parsing_pyqs', label: 'Extracting PYQ Question Units', description: 'Parsing sections, question blocks, and raw mark distributions across years' },
  { id: 'embedding', label: 'Generating Sentence Embeddings', description: 'Applying all-MiniLM-L6-v2 to group semantically identical and rephrased questions' },
  { id: 'saving', label: 'Indexing Topic Frequency Weights', description: 'Calculating repeat frequency score and marks weight metrics' },
  { id: 'planning', label: 'Executing Knapsack Marks Optimizer', description: 'Solving 0/1 knapsack optimization for marks-yield efficiency' },
  { id: 'generating_papers', label: 'Synthesizing Pattern-Synced Mock Papers', description: 'Replicating section patterns and formatting printable exam papers' },
  { id: 'done', label: 'Analysis Complete', description: 'Dashboard, revision timeline, and simulated papers are ready' },
]

export default function Processing() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()

  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return

    let isMounted = true
    let intervalId: any = null

    const checkStatus = async () => {
      try {
        const resp = await pollStatus(jobId)
        if (!isMounted) return

        setStatus(resp)

        if (resp.status === 'done') {
          clearInterval(intervalId)
          // Store result in sessionStorage for instant retrieval if needed
          if (resp.result) {
            sessionStorage.setItem(`precedent_result_${resp.result.subject_id || jobId}`, JSON.stringify(resp.result))
          }
          // Give user a brief moment to see 100% complete before automatic redirect
          setTimeout(() => {
            const targetId = resp.result?.subject_id || jobId
            navigate(`/dashboard/${targetId}`)
          }, 1200)
        } else if (resp.status === 'error') {
          clearInterval(intervalId)
          setError(resp.stage_message || 'An error occurred during pattern processing.')
        }
      } catch (err: any) {
        if (!isMounted) return
        console.error('Polling error:', err)
        // If 404 or backend unavailable, wait and retry
      }
    }

    // Immediate initial call
    checkStatus()
    intervalId = setInterval(checkStatus, 1800)

    return () => {
      isMounted = false
      if (intervalId) clearInterval(intervalId)
    }
  }, [jobId, navigate])

  const currentStep = status?.status || 'pending'
  const progress = status?.progress ?? 5

  return (
    <div className="pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-12 h-12 bg-navy rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-card">
          <BookOpen size={24} className="text-gold animate-pulse" />
        </div>
        <h1 className="font-display text-3xl font-bold text-navy">
          Decoding Your Exam Pattern
        </h1>
        <p className="text-sm text-navy-500 mt-2">
          {status?.stage_message || 'Connecting to Precedent pattern inference engine...'}
        </p>
      </div>

      {error ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card border-red-200 bg-red-50/50 p-6 text-center space-y-4"
        >
          <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
            <AlertCircle size={24} />
          </div>
          <div>
            <h3 className="font-display text-lg font-bold text-red-900">Analysis Halted</h3>
            <p className="text-xs text-red-700 mt-1 max-w-md mx-auto leading-relaxed">
              {error}
            </p>
            <p className="text-[11px] text-red-500 mt-2">
              Tip: If you uploaded a scanned image PDF, please ensure the text can be selected and copied, or export it using searchable OCR.
            </p>
          </div>
          <div className="pt-2">
            <button
              onClick={() => navigate('/upload')}
              className="btn-primary text-xs py-2.5 px-6 inline-flex items-center gap-2"
            >
              <RefreshCw size={14} /> Return to Upload
            </button>
          </div>
        </motion.div>
      ) : (
        <div className="card space-y-6">
          <ProgressStep
            steps={PIPELINE_STEPS}
            currentStep={currentStep}
            progress={progress}
          />

          {status?.status === 'done' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="pt-4 text-center border-t border-navy-50"
            >
              <button
                onClick={() => {
                  const targetId = status?.result?.subject_id || jobId
                  navigate(`/dashboard/${targetId}`)
                }}
                className="btn-primary text-sm inline-flex items-center gap-2 py-2.5 px-6"
              >
                Proceed to Dashboard <ArrowRight size={16} />
              </button>
            </motion.div>
          )}
        </div>
      )}
    </div>
  )
}
