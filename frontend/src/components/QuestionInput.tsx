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
        className={`flex items-end gap-3 rounded-xl border border-border bg-muted shadow-inner transition-colors focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 ${
          compact ? 'p-2' : 'p-3 sm:p-4'
        }`}
      >
        <textarea
          aria-label="Ask a FAR/AIM question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={compact ? 1 : 2}
          className="max-h-32 min-h-12 flex-1 resize-none bg-transparent px-1 py-3 text-base text-foreground outline-none placeholder:text-muted-foreground disabled:opacity-70 sm:text-lg"
        />
        <button
          type="submit"
          disabled={!question.trim() || disabled}
          className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-all hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:opacity-45"
          aria-label="Submit question"
        >
          <ArrowRight className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>
    </form>
  )
}
