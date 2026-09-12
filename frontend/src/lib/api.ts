import axios from 'axios'
import type {
  SubmissionResponse, StatusResponse, PlannerResponse,
  MockPapersResponse, PublishResponse, RepositoryResponse, TopicItem,
} from './types'

const BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: BASE,
  timeout: 120_000,
})

// ── Upload ────────────────────────────────────────────────────────────────────

export async function uploadFiles(form: FormData): Promise<SubmissionResponse> {
  const { data } = await api.post<SubmissionResponse>('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function pollStatus(jobId: string): Promise<StatusResponse> {
  const { data } = await api.get<StatusResponse>(`/api/status/${jobId}`)
  return data
}

// ── Planner ───────────────────────────────────────────────────────────────────

export async function createRevisionPlan(
  subject_id: string,
  days_available: number,
  hours_per_day: number,
  topics?: TopicItem[],
): Promise<PlannerResponse> {
  const { data } = await api.post<PlannerResponse>('/api/planner', {
    subject_id,
    days_available,
    hours_per_day,
    topics,
  })
  return data
}

// ── Papers ────────────────────────────────────────────────────────────────────

export async function getMockPapers(subjectId: string): Promise<MockPapersResponse> {
  const { data } = await api.get<MockPapersResponse>(`/api/papers/${subjectId}`)
  return data
}

export function getPaperDownloadUrl(subjectId: string, paperNumber: number): string {
  return `${BASE}/api/papers/${subjectId}/download/${paperNumber}`
}

// ── GitHub ────────────────────────────────────────────────────────────────────

export async function publishToGitHub(submissionId: string): Promise<PublishResponse> {
  const { data } = await api.post<PublishResponse>(`/api/publish/${submissionId}`)
  return data
}

export async function getRepository(): Promise<RepositoryResponse> {
  const { data } = await api.get<RepositoryResponse>('/api/repository')
  return data
}

// ── GitHub API (public, no token needed for public repos) ─────────────────────

const GITHUB_REPO = import.meta.env.VITE_GITHUB_REPO || ''

export async function getRepoStats(): Promise<{ subjects: number; institutions: number; papers: number }> {
  // 1. Try local backend first (has authenticated GitHub API token)
  try {
    const res = await getRepository()
    if (res && (res.total_subjects > 0 || res.total_institutions > 0)) {
      return {
        subjects: res.total_subjects,
        institutions: res.total_institutions,
        papers: res.total_papers || res.total_pyqs || 0,
      }
    }
  } catch {
    // Fall back to direct GitHub public API
  }

  // 2. Direct GitHub public tree API fallback
  if (!GITHUB_REPO) return { subjects: 0, institutions: 0, papers: 0 }
  try {
    const { data } = await axios.get(
      `https://api.github.com/repos/${GITHUB_REPO}/git/trees/main?recursive=1`,
      { timeout: 10_000 }
    )
    const tree: { path: string; type: string }[] = data.tree || []
    const institutions = new Set<string>()
    const subjects = new Set<string>()
    let papers = 0

    const SKIP = new Set(['precedent-repository', '.git', '.github'])

    for (const node of tree) {
      const parts = node.path.split('/')
      if (parts[0] && SKIP.has(parts[0])) continue

      // Count PDF papers (PYQs and generated mock papers)
      if (node.type === 'blob' && node.path.endsWith('.pdf')) {
        papers++
      }

      // Root-level directory = Institution
      if (parts.length === 1 && node.type === 'tree') {
        institutions.add(parts[0])
      }
      // Depth-2 directory = Subject
      if (parts.length === 2 && node.type === 'tree') {
        institutions.add(parts[0])
        subjects.add(`${parts[0]}/${parts[1]}`)
      }
    }
    return {
      subjects: subjects.size,
      institutions: institutions.size,
      papers,
    }
  } catch {
    return { subjects: 0, institutions: 0, papers: 0 }
  }
}

