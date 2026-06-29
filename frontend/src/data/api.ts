import type { MockFarsightResponse } from '../types/farsight'

type ApiCitation = {
  document: string
  section_number: string
  section_title: string
  page_number: number | null
  corpus_version: string | null
}

type ApiResponse = {
  found: boolean
  answer: string
  excerpt: string | null
  citation: ApiCitation | null
}

function mapApiResponse(api: ApiResponse): MockFarsightResponse {
  if (api.found && api.excerpt && api.citation) {
    return {
      found: true,
      answer: api.answer,
      excerpt: api.excerpt,
      citation: {
        document: api.citation.document,
        sectionNumber: api.citation.section_number,
        sectionTitle: api.citation.section_title,
        pageNumber: api.citation.page_number ?? undefined,
        corpusVersion: api.citation.corpus_version ?? undefined,
      },
    }
  }

  return {
    found: false,
    answer: api.answer,
    excerpt: null,
    citation: null,
  }
}

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function askFarsight(question: string): Promise<MockFarsightResponse> {
  const response = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

  if (!response.ok) {
    throw new ApiError(
      response.status >= 500
        ? 'Having trouble reaching the regulations right now. Please try again in a moment.'
        : 'Something went wrong with that request. Please try a different question.',
    )
  }

  const data: ApiResponse = await response.json()
  return mapApiResponse(data)
}
