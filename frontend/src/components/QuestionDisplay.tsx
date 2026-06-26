import { BrandPill } from './BrandPill'

type QuestionDisplayProps = {
  question: string
}

export function QuestionDisplay({ question }: QuestionDisplayProps) {
  return (
    <section className="rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8">
      <BrandPill>Your question</BrandPill>
      <h1 className="mt-5 text-3xl font-semibold leading-tight text-foreground sm:text-4xl">
        {question}
      </h1>
    </section>
  )
}
