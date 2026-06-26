import { BookOpen, Quote } from 'lucide-react'
import type { Citation } from '../types/farsight'

type AnswerCardProps = {
  answer: string
  excerpt: string
  citation: Citation
}

export function AnswerCard({ answer, excerpt, citation }: AnswerCardProps) {
  return (
    <article className="rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8">
      <p className="text-lg leading-relaxed text-foreground sm:text-xl">{answer}</p>

      <div className="my-8 h-px bg-border" />

      <div className="rounded-lg border border-accent/20 bg-accent/5 p-4">
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <BookOpen className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium uppercase tracking-wider text-accent">
              Official source
            </p>
            <h2 className="mt-2 text-lg font-semibold leading-snug text-foreground">
              {citation.document} {citation.sectionNumber} - {citation.sectionTitle}
            </h2>
            <div className="mt-4 rounded-lg border border-accent/10 bg-card/70 p-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-accent">
                <Quote className="h-4 w-4" aria-hidden="true" />
                Verified excerpt
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{excerpt}</p>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Citation assembled from chunk metadata, not model text.
            </p>
          </div>
        </div>
      </div>
    </article>
  )
}
