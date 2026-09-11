// ── Shared TypeScript types for Precedent ─────────────────────────────────────

export interface TopicItem {
  id?: string
  name: string
  frequency_score: number      // 0–1
  marks_weight: number         // 0–1 (normalised)
  appeared_in_years: number[]
  prep_time_hrs: number
}

export interface TopicsResponse {
  subject_id: string
  subject_name: string
  total_years_analyzed: number
  topics: TopicItem[]
}

export interface DayPlan {
  day: number
  topics: TopicItem[]
  total_hours: number
}

export interface PlannerResponse {
  plan_id?: string
  subject_id: string
  days_available: number
  hours_per_day: number
  expected_marks_coverage: number  // 0–1
  days: DayPlan[]
}

export interface Question {
  number: string
  text: string
  marks: number
  type: 'MCQ' | 'short' | 'long'
}

export interface Section {
  title: string
  instructions: string
  questions: Question[]
  total_marks: number
}

export interface MockPaper {
  paper_number: number
  subject: string
  course: string
  institution: string
  exam_duration: string
  total_marks: number
  sections: Section[]
  generated_at: string
}

export interface MockPapersResponse {
  submission_id: string
  papers: MockPaper[]
}

export interface SubmissionResponse {
  submission_id: string
  subject_id: string
  status: string
  message: string
}

export interface StatusResponse {
  submission_id: string
  status: string
  stage_message: string
  progress: number
  result?: AnalysisResult
}

export interface AnalysisResult {
  submission_id: string
  subject_id: string
  topics: TopicItem[]
  plan: PlannerResponse
  papers: MockPaper[]
  total_years: number
}

export interface PublishResponse {
  success: boolean
  github_url: string
  commit_sha: string
  files_committed: string[]
}

export interface RepoSubject {
  name: string
  path: string
  github_url: string
}

export interface RepoCourse {
  name: string
  subjects: RepoSubject[]
}

export interface RepoInstitution {
  name: string
  courses: RepoCourse[]
}

export interface RepositoryResponse {
  institutions: RepoInstitution[]
  total_subjects: number
  total_institutions: number
}
