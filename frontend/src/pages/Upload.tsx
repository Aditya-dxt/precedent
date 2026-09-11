import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { Sparkles, AlertCircle, ArrowRight, ShieldCheck, FileText, AlignLeft } from 'lucide-react'
import UploadZone from '../components/UploadZone'
import { uploadFiles } from '../lib/api'

export default function Upload() {
  const navigate = useNavigate()

  // Academic metadata
  const [institution, setInstitution] = useState('')
  const [courseName, setCourseName] = useState('')
  const [courseCode, setCourseCode] = useState('')
  const [subjectName, setSubjectName] = useState('')

  // Files & Syllabus
  const [syllabusMode, setSyllabusMode] = useState<'pdf' | 'text'>('pdf')
  const [syllabusFiles, setSyllabusFiles] = useState<File[]>([])
  const [syllabusText, setSyllabusText] = useState('')
  const [pyqFiles, setPyqFiles] = useState<File[]>([])
  const [pyqYears, setPyqYears] = useState<{ [filename: string]: number }>({})

  // Form submission state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleYearChange = (filename: string, year: number) => {
    setPyqYears(prev => ({ ...prev, [filename]: year }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!institution.trim() || !courseName.trim() || !courseCode.trim() || !subjectName.trim()) {
      setError('Please fill in all academic details (Institution, Course, Code, and Subject).')
      return
    }

    if (syllabusMode === 'pdf' && syllabusFiles.length === 0) {
      setError('Please upload the official Syllabus PDF for this subject.')
      return
    }

    if (syllabusMode === 'text' && !syllabusText.trim()) {
      setError('Please enter or paste the syllabus text content for this subject.')
      return
    }

    if (pyqFiles.length === 0) {
      setError('Please upload at least one Previous Year Question (PYQ) PDF.')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('institution_name', institution.trim())
      formData.append('course_name', courseName.trim())
      formData.append('course_code', courseCode.trim())
      formData.append('subject_name', subjectName.trim())

      // Syllabus (either PDF or raw text)
      if (syllabusMode === 'pdf') {
        formData.append('syllabus', syllabusFiles[0])
      } else {
        formData.append('syllabus_text', syllabusText.trim())
      }

      // PYQs
      const currentYear = new Date().getFullYear()
      const yearList: number[] = []

      pyqFiles.forEach((file, idx) => {
        formData.append('pyqs', file)
        const yr = pyqYears[file.name] || (currentYear - (idx + 1))
        yearList.push(yr)
      })

      formData.append('years', yearList.join(','))

      const resp = await uploadFiles(formData)

      if (resp && resp.submission_id) {
        navigate(`/processing/${resp.submission_id}`)
      } else {
        throw new Error(resp.message || 'Failed to initiate analysis pipeline.')
      }
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || err.message || 'An error occurred while uploading. Please ensure valid text-extractable PDFs.')
      setLoading(false)
    }
  }

  return (
    <div className="pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <span className="text-xs uppercase tracking-widest text-gold font-bold">Step 1 of 4</span>
        <h1 className="font-display text-3xl sm:text-4xl font-bold text-navy mt-1">
          Ingest Syllabus & Previous Question Papers
        </h1>
        <p className="text-sm text-navy-600 mt-2">
          Precedent will parse the topic modules, extract question units, and train lightweight sentence-embedding clusters on your actual syllabus structure.
        </p>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3"
        >
          <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Analysis Ingestion Notice</p>
            <p className="text-xs mt-0.5">{error}</p>
          </div>
        </motion.div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Academic Scope */}
        <div className="card space-y-4">
          <div className="border-b border-navy-50 pb-2">
            <h2 className="font-display text-lg font-bold text-navy">1. Academic Program Identification</h2>
            <p className="text-xs text-navy-400">Specify your university and subject scope for public repository archiving.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-navy mb-1">
                Institution / University <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Dr. A.P.J. Abdul Kalam Technical University"
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-navy-200 text-sm focus:outline-none focus:border-navy text-navy"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-navy mb-1">
                Course / Degree Program <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. B.Tech Computer Science & Engineering"
                value={courseName}
                onChange={(e) => setCourseName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-navy-200 text-sm focus:outline-none focus:border-navy text-navy"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-navy mb-1">
                Course Code <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. BCS401"
                value={courseCode}
                onChange={(e) => setCourseCode(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-navy-200 text-sm focus:outline-none focus:border-navy text-navy"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-navy mb-1">
                Subject Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Database Management Systems"
                value={subjectName}
                onChange={(e) => setSubjectName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-navy-200 text-sm focus:outline-none focus:border-navy text-navy"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Syllabus Input (PDF or Text) */}
        <div className="card space-y-4">
          <div className="border-b border-navy-50 pb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-lg font-bold text-navy">2. Official Syllabus Input</h2>
              <p className="text-xs text-navy-400">Choose to upload an official PDF document or paste the text directly.</p>
            </div>

            {/* Mode Switcher Tabs */}
            <div className="flex items-center p-1 bg-navy-50 rounded-xl w-fit">
              <button
                type="button"
                onClick={() => setSyllabusMode('pdf')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  syllabusMode === 'pdf' ? 'bg-white text-navy shadow-xs' : 'text-navy-500 hover:text-navy'
                }`}
              >
                <FileText size={13} /> Upload PDF
              </button>
              <button
                type="button"
                onClick={() => setSyllabusMode('text')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  syllabusMode === 'text' ? 'bg-white text-navy shadow-xs' : 'text-navy-500 hover:text-navy'
                }`}
              >
                <AlignLeft size={13} /> Enter as Text
              </button>
            </div>
          </div>

          {syllabusMode === 'pdf' ? (
            <UploadZone
              label="Upload Syllabus PDF"
              description="Upload the official unit/module syllabus published by your university"
              required
              files={syllabusFiles}
              onFilesChange={setSyllabusFiles}
            />
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-navy">
                  Paste or Type Syllabus Curriculum <span className="text-red-500">*</span>
                </label>
                <span className="text-xs text-navy-400">Supports units, modules & topic lists</span>
              </div>
              <textarea
                rows={8}
                required={syllabusMode === 'text'}
                placeholder={`Paste your syllabus units and chapters here... For example:

UNIT 1: Database System Concepts and Architecture, Data Models, Schemas and Instances, ER Model, Entity Types, Relationship Types, Weak Entities.
UNIT 2: Relational Data Model and Relational Database Constraints, Relational Algebra and Relational Calculus, SQL DDL/DML, Nested Queries, Aggregate Functions.
UNIT 3: Functional Dependencies and Normalization, 1NF, 2NF, 3NF, BCNF, Multi-valued Dependencies and 4NF.
UNIT 4: Transaction Processing, ACID Properties, Schedules and Serializability, Concurrency Control Protocols (Two-Phase Locking, Timestamp Ordering), Deadlock Handling.
UNIT 5: Storage and Indexing, Single-Level and Multi-Level Indexing, B-Trees and B+ Trees, Query Optimization Basics.`}
                value={syllabusText}
                onChange={(e) => setSyllabusText(e.target.value)}
                className="w-full p-4 rounded-xl border border-navy-200 text-sm font-normal text-navy placeholder:text-navy-300 focus:outline-none focus:border-navy leading-relaxed bg-white"
              />
              <p className="text-[11px] text-navy-400">
                Tip: You can include Unit I, Unit II, or Module headings — the pattern engine will automatically discover all underlying topics.
              </p>
            </div>
          )}
        </div>

        {/* Section 3: PYQs Upload */}
        <div className="card space-y-4">
          <div className="border-b border-navy-50 pb-2">
            <h2 className="font-display text-lg font-bold text-navy">3. Historical Previous Year Question Papers (PYQs)</h2>
            <p className="text-xs text-navy-400">Upload 1 to 5 years of exam papers. Tag each PDF with its corresponding exam year.</p>
          </div>

          <UploadZone
            label="Upload Previous Year Papers (Tagged by Year)"
            description="Drag and drop multiple question papers from past examination cycles"
            required
            multiple
            yearTagging
            years={pyqYears}
            onYearChange={handleYearChange}
            files={pyqFiles}
            onFilesChange={setPyqFiles}
          />
        </div>

        {/* Action button */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <div className="flex items-center gap-2 text-xs text-navy-500">
            <ShieldCheck size={16} className="text-green-600" />
            <span>Files will be indexed and committed to Precedent's institutional knowledge graph.</span>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto btn-primary flex items-center justify-center gap-2 py-3.5 px-8 disabled:opacity-50"
          >
            {loading ? (
              <span>Uploading & Initializing...</span>
            ) : (
              <>
                <span>Run Exam History Analysis</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
