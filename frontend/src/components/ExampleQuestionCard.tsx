import { ArrowUpRight } from 'lucide-react'

type ExampleQuestionCardProps = {
  question: string
  onSelect: (question: string) => void
}

export function ExampleQuestionCard({ question, onSelect }: ExampleQuestionCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(question)}
      className="group flex min-h-20 items-start justify-between gap-3 rounded-xl border border-border/80 bg-card p-4 text-left text-[15px] font-medium leading-snug text-foreground transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-[var(--shadow-md)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring sm:text-base"
      style={{ boxShadow: 'var(--shadow-sm)' }}
    >
      <span>{question}</span>
      <ArrowUpRight
        className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground/40 transition-all group-hover:text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
        aria-hidden="true"
      />
    </button>
  )
}
