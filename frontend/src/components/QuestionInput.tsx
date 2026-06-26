import { ArrowRight } from 'lucide-react'
import { type FormEvent, type KeyboardEvent, useState } from 'react'

type QuestionInputProps = {
  onSubmit: (question: string) => void
  placeholder?: string
  disabled?: boolean
  compact?: boolean
}

export function QuestionInput({
  onSubmit,
  placeholder = 'Ask anything about FAA regulations...',
  disabled = false,
  compact = false,
}: QuestionInputProps) {
  const [question, setQuestion] = useState('')

  function submitQuestion(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || disabled) {
      return
    }

    onSubmit(trimmedQuestion)
    setQuestion('')
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submitQuestion()
    }
  }

  return (
    <form onSubmit={submitQuestion} className="w-full">
      <div
        className={`flex items-end gap-3 rounded-2xl border border-border bg-card transition-all focus-within:border-primary/40 focus-within:shadow-[var(--shadow-glow)] ${
          compact ? 'p-2' : 'p-3 sm:p-4'
        }`}
        style={{ boxShadow: 'var(--shadow-md)' }}
      >
        <textarea
          aria-label="Ask a FAR/AIM question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={compact ? 1 : 2}
          className="max-h-32 min-h-12 flex-1 resize-none bg-transparent px-2 py-3 text-base text-foreground outline-none placeholder:text-muted-foreground/60 disabled:opacity-70 sm:text-lg"
        />
        <button
          type="submit"
          disabled={!question.trim() || disabled}
          className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-hover text-primary-foreground shadow-sm transition-all hover:shadow-md active:scale-95 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:opacity-40 disabled:shadow-none"
          aria-label="Submit question"
        >
          <ArrowRight className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>
    </form>
  )
}
