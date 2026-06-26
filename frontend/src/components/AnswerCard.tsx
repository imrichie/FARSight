import { motion } from 'motion/react'
import { BookOpen, Quote, Shield } from 'lucide-react'
import type { Citation } from '../types/farsight'

type AnswerCardProps = {
  answer: string
  excerpt: string
  citation: Citation
}

export function AnswerCard({ answer, excerpt, citation }: AnswerCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="rounded-2xl border border-border/60 bg-card p-6 sm:p-8"
      style={{ boxShadow: 'var(--shadow-md)' }}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary-hover">
          <Shield className="h-4 w-4 text-white" aria-hidden="true" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">
            Grounded Answer
          </p>
          <p className="mt-3 text-lg leading-relaxed text-foreground">{answer}</p>
        </div>
      </div>

      <div className="my-8 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

      <div
        className="rounded-xl border border-accent/15 p-5 sm:p-6"
        style={{
          background:
            'linear-gradient(135deg, rgba(12, 74, 110, 0.04) 0%, rgba(12, 74, 110, 0.02) 100%)',
        }}
      >
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <BookOpen className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-accent">
              Official source
            </p>
            <h2 className="mt-2 text-lg font-bold leading-snug tracking-tight text-foreground">
              {citation.document} {citation.sectionNumber}
            </h2>
            <p className="mt-0.5 text-sm text-muted-foreground">{citation.sectionTitle}</p>

            <div className="mt-4 rounded-lg border border-accent/10 bg-card/80 p-4 backdrop-blur-sm">
              <div className="mb-2.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent/70">
                <Quote className="h-3.5 w-3.5" aria-hidden="true" />
                Verified excerpt
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground italic">{excerpt}</p>
            </div>

            <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground/70">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Citation from chunk metadata, not model output
            </p>
          </div>
        </div>
      </div>
    </motion.article>
  )
}
