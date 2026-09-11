import React, { useState } from 'react'
import { ChevronRight, ChevronDown, Folder, FileText, ExternalLink, GraduationCap, BookOpen } from 'lucide-react'
import type { RepoInstitution } from '../lib/types'

interface RepoTreeProps {
  institutions: RepoInstitution[]
  loading?: boolean
}

export default function RepoTree({ institutions, loading }: RepoTreeProps) {
  const [openInstitutions, setOpenInstitutions] = useState<{ [key: string]: boolean }>({
    '0': true, // default first one expanded if present
  })
  const [openCourses, setOpenCourses] = useState<{ [key: string]: boolean }>({
    '0-0': true,
  })

  const toggleInst = (key: string) => {
    setOpenInstitutions(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const toggleCourse = (key: string) => {
    setOpenCourses(prev => ({ ...prev, [key]: !prev[key] }))
  }

  if (loading) {
    return (
      <div className="p-12 text-center text-navy-400 animate-pulse">
        <div className="w-12 h-12 border-4 border-navy-200 border-t-navy rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm font-medium">Fetching public academic repository index...</p>
      </div>
    )
  }

  if (!institutions || institutions.length === 0) {
    return (
      <div className="p-12 text-center bg-white rounded-2xl border border-navy-100 shadow-xs">
        <Folder size={40} className="mx-auto text-navy-300 mb-3" />
        <h3 className="font-display text-lg font-semibold text-navy">No Subjects Published Yet</h3>
        <p className="text-sm text-navy-500 mt-1 max-w-md mx-auto">
          Be the first student to upload a syllabus and past papers to seed your university repository branch.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-navy-100 shadow-card p-6 divide-y divide-navy-50">
      {institutions.map((inst, iIdx) => {
        const instKey = `${iIdx}`
        const isInstOpen = !!openInstitutions[instKey]

        return (
          <div key={instKey} className="py-4 first:pt-0 last:pb-0">
            {/* Institution Row */}
            <button
              onClick={() => toggleInst(instKey)}
              className="w-full flex items-center justify-between text-left py-2 px-3 rounded-xl hover:bg-navy-50/50 transition-colors group"
            >
              <div className="flex items-center gap-2.5">
                {isInstOpen ? (
                  <ChevronDown size={18} className="text-navy-400 group-hover:text-navy" />
                ) : (
                  <ChevronRight size={18} className="text-navy-400 group-hover:text-navy" />
                )}
                <GraduationCap size={20} className="text-gold" />
                <span className="font-display text-base font-bold text-navy">
                  {inst.name}
                </span>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-navy-50 text-navy-600">
                {inst.courses.length} {inst.courses.length === 1 ? 'Program' : 'Programs'}
              </span>
            </button>

            {/* Courses list */}
            {isInstOpen && (
              <div className="ml-6 pl-4 border-l border-navy-100 mt-2 space-y-2">
                {inst.courses.map((course, cIdx) => {
                  const courseKey = `${iIdx}-${cIdx}`
                  const isCourseOpen = !!openCourses[courseKey]

                  return (
                    <div key={courseKey} className="py-1">
                      <button
                        onClick={() => toggleCourse(courseKey)}
                        className="w-full flex items-center justify-between text-left py-1.5 px-3 rounded-lg hover:bg-navy-50/40 transition-colors text-sm"
                      >
                        <div className="flex items-center gap-2">
                          {isCourseOpen ? (
                            <ChevronDown size={16} className="text-navy-400" />
                          ) : (
                            <ChevronRight size={16} className="text-navy-400" />
                          )}
                          <BookOpen size={16} className="text-navy-500" />
                          <span className="font-medium text-navy-800">
                            {course.name}
                          </span>
                        </div>
                        <span className="text-xs text-navy-400">
                          {course.subjects.length} {course.subjects.length === 1 ? 'Subject' : 'Subjects'}
                        </span>
                      </button>

                      {/* Subjects list */}
                      {isCourseOpen && (
                        <div className="ml-6 pl-4 border-l border-gold-200 mt-1 space-y-1.5">
                          {course.subjects.map((sub, sIdx) => (
                            <div
                              key={sIdx}
                              className="flex items-center justify-between p-2 rounded-lg bg-offwhite/50 hover:bg-offwhite border border-navy-50 transition-colors"
                            >
                              <div className="flex items-center gap-2 min-w-0">
                                <FileText size={15} className="text-gold-600 flex-shrink-0" />
                                <span className="text-xs font-medium text-navy truncate">
                                  {sub.name}
                                </span>
                              </div>

                              {sub.github_url && sub.github_url !== '#' && (
                                <a
                                  href={sub.github_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="flex items-center gap-1 text-[11px] font-semibold text-navy hover:text-gold transition-colors ml-2 flex-shrink-0"
                                >
                                  Browse Artifacts <ExternalLink size={12} />
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
