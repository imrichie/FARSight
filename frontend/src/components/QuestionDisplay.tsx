import { BrandPill } from './BrandPill'

type QuestionDisplayProps = {
  question: string
}

export function QuestionDisplay({ question }: QuestionDisplayProps) {
  return (
    <section
      className="rounded-2xl border border-border/60 bg-card p-6 sm:p-8"
      style={{ boxShadow: 'var(--shadow-sm)' }}
    >
      <BrandPill>Your question</BrandPill>
      <h1 className="mt-5 text-2xl font-bold leading-snug tracking-tight text-foreground sm:text-3xl">
        {question}
      </h1>
    </section>
  )
}
