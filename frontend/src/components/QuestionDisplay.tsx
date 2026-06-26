import { MessageCircle } from 'lucide-react'

type QuestionDisplayProps = {
  question: string
}

export function QuestionDisplay({ question }: QuestionDisplayProps) {
  return (
    <section
      className="rounded-2xl border border-border/60 bg-card p-6 sm:p-8"
      style={{ boxShadow: 'var(--shadow-sm)' }}
    >
      <span className="inline-flex items-center gap-2 rounded-full bg-accent/8 px-3.5 py-1.5 text-xs font-semibold uppercase tracking-wider text-accent border border-accent/15">
        <MessageCircle className="h-3.5 w-3.5" aria-hidden="true" />
        Your question
      </span>
      <h1 className="mt-5 text-2xl font-bold leading-snug tracking-tight text-foreground sm:text-3xl">
        {question}
      </h1>
    </section>
  )
}
