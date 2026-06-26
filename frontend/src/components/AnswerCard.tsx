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
      className="overflow-hidden rounded-2xl border border-border/60 bg-card"
      style={{ boxShadow: 'var(--shadow-md)' }}
    >
      <div className="p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-hover shadow-sm">
            <Shield className="h-4.5 w-4.5 text-white" aria-hidden="true" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Grounded Answer
            </p>
            <p className="mt-3 text-lg leading-relaxed text-foreground">{answer}</p>
          </div>
        </div>
      </div>

      <div
        className="border-t border-accent/10 p-6 sm:p-8"
        style={{
          background:
            'linear-gradient(145deg, rgba(12, 74, 110, 0.05) 0%, rgba(12, 74, 110, 0.02) 100%)',
        }}
      >
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent/12 text-accent shadow-sm">
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

            <div className="mt-4 rounded-xl border border-accent/10 bg-card/80 p-4 backdrop-blur-sm">
              <div className="mb-2.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent/70">
                <Quote className="h-3.5 w-3.5" aria-hidden="true" />
                Verified excerpt
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground italic">{excerpt}</p>
            </div>
          </div>
        </div>
      </div>
    </motion.article>
  )
}
