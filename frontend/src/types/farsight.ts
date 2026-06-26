export type Citation = {
  document: string
  sectionNumber: string
  sectionTitle: string
  pageNumber?: number
  corpusVersion?: string
}

export type MockFarsightResponse =
  | {
      found: true
      answer: string
      excerpt: string
      citation: Citation
    }
  | {
      found: false
      answer: string
      excerpt: null
      citation: null
    }
