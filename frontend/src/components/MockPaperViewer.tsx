import React from 'react'
import { Printer, Download, Award, Clock, FileCheck } from 'lucide-react'
import type { MockPaper } from '../lib/types'
import { getPaperDownloadUrl } from '../lib/api'

interface MockPaperViewerProps {
  paper: MockPaper
  subjectId: string
}

export default function MockPaperViewer({ paper, subjectId }: MockPaperViewerProps) {
  const handlePrint = () => {
    window.print()
  }

  const downloadUrl = getPaperDownloadUrl(subjectId, paper.paper_number)

  return (
    <div className="space-y-4">
      {/* Action Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-xl border border-navy-100 shadow-xs print:hidden">
        <div className="flex items-center gap-2">
          <span className="bg-navy text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            Mock Paper {paper.paper_number}
          </span>
          <span className="text-xs text-navy-500 font-medium flex items-center gap-1">
            <Clock size={14} /> {paper.exam_duration || '3 Hours'}
          </span>
          <span className="text-xs text-navy-500 font-medium flex items-center gap-1">
            <Award size={14} /> {paper.total_marks} Marks
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-navy-200 text-xs font-medium text-navy hover:bg-navy-50 transition-colors"
          >
            <Printer size={14} /> Print Exam Sheet
          </button>
          <a
            href={downloadUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy text-xs font-medium text-white hover:bg-navy-700 transition-colors shadow-xs"
          >
            <Download size={14} /> Download PDF
          </a>
        </div>
      </div>

      {/* Realistic University Exam Paper Layout */}
      <div className="bg-white text-navy p-8 md:p-12 rounded-2xl shadow-card border border-navy-100 print:shadow-none print:border-none print:p-0">
        {/* Paper Header */}
        <div className="text-center border-b-2 border-navy-800 pb-4 mb-6">
          <p className="text-xs uppercase tracking-widest text-navy-500 font-semibold mb-1">
            Official Simulated Examination Paper
          </p>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-navy uppercase tracking-tight">
            {paper.institution || 'University Examination'}
          </h2>
          <p className="text-sm font-semibold text-navy-700 mt-1">
            {paper.course} — Semester End Examination
          </p>
          <div className="inline-block mt-2 px-4 py-0.5 border border-navy-300 rounded text-xs font-bold uppercase tracking-wider text-navy">
            Subject: {paper.subject}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-medium text-navy-600 mt-4 pt-3 border-t border-navy-100 text-left md:text-center">
            <div><span className="text-navy-400">Time Allowed:</span> {paper.exam_duration || '3 Hours'}</div>
            <div><span className="text-navy-400">Maximum Marks:</span> {paper.total_marks}</div>
            <div><span className="text-navy-400">Paper Set:</span> 0{paper.paper_number}</div>
            <div><span className="text-navy-400">Pattern:</span> PYQ Synced</div>
          </div>
        </div>

        {/* General Instructions */}
        <div className="bg-offwhite/70 p-3.5 rounded-lg text-xs text-navy-700 mb-8 border border-navy-100">
          <p className="font-semibold text-navy mb-1">General Instructions to Candidates:</p>
          <ol className="list-decimal list-inside space-y-0.5 text-navy-600">
            <li>Check that this question paper contains all designated sections before answering.</li>
            <li>All questions within compulsory sections must be attempted as instructed.</li>
            <li>Marks for each question or sub-part are indicated on the right margin.</li>
            <li>Assume standard notations and suitable data if necessary, stating assumptions clearly.</li>
          </ol>
        </div>

        {/* Sections & Questions */}
        <div className="space-y-8">
          {paper.sections.map((sec, sIdx) => (
            <div key={sIdx} className="space-y-4">
              <div className="border-b border-navy-200 pb-1.5 flex flex-wrap items-baseline justify-between">
                <h3 className="font-display text-lg font-bold text-navy uppercase tracking-wide">
                  {sec.title}
                </h3>
                <span className="text-xs font-bold text-gold-600">
                  [{sec.total_marks} Marks]
                </span>
              </div>
              <p className="text-xs italic text-navy-500 mb-3">
                {sec.instructions}
              </p>

              <div className="space-y-4 divide-y divide-navy-50">
                {sec.questions.map((q, qIdx) => (
                  <div key={qIdx} className="pt-3 first:pt-0 flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 min-w-0">
                      <span className="font-bold text-sm text-navy w-8 flex-shrink-0">
                        {q.number || `Q${qIdx + 1}`}.
                      </span>
                      <p className="text-sm text-navy-900 leading-relaxed">
                        {q.text}
                      </p>
                    </div>
                    <div className="text-xs font-bold text-navy-600 flex-shrink-0 bg-navy-50 px-2 py-0.5 rounded">
                      [{q.marks}M]
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer in exam layout */}
        <div className="mt-12 pt-6 border-t-2 border-navy-800 text-center">
          <p className="text-xs uppercase tracking-widest text-navy-400 font-semibold">
            *** END OF EXAMINATION PAPER ***
          </p>
          <p className="text-[10px] text-navy-400 mt-1 font-mono">
            Generated via Precedent Academic Intelligence Engine
          </p>
        </div>
      </div>
    </div>
  )
}
