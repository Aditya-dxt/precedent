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

export async function getRepoStats(): Promise<{ subjects: number; institutions: number }> {
  if (!GITHUB_REPO) return { subjects: 0, institutions: 0 }
  try {
    const { data } = await axios.get(
      `https://api.github.com/repos/${GITHUB_REPO}/git/trees/main?recursive=1`,
      { timeout: 10_000 }
    )
    const tree: { path: string; type: string }[] = data.tree || []
    // Count unique institution dirs (depth 2) and subject dirs (depth 4)
    const institutions = new Set<string>()
    const subjects = new Set<string>()
    for (const node of tree) {
      const parts = node.path.split('/')
      if (parts[0] === 'precedent-repository') {
        if (parts.length === 2 && node.type === 'tree') institutions.add(parts[1])
        if (parts.length === 4 && node.type === 'tree') subjects.add(node.path)
      }
    }
    return { subjects: subjects.size, institutions: institutions.size }
  } catch {
    return { subjects: 0, institutions: 0 }
  }
}
