type ExampleQuestionCardProps = {
  question: string
  onSelect: (question: string) => void
}

export function ExampleQuestionCard({ question, onSelect }: ExampleQuestionCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(question)}
      className="min-h-24 rounded-xl border border-border bg-card p-4 text-left text-base font-medium leading-snug text-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:bg-primary/5 hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring sm:text-lg"
    >
      {question}
    </button>
  )
}
