import { useEffect, useRef } from 'react'
import { AnswerCard } from '../components/AnswerCard'
import { ErrorState } from '../components/ErrorState'
import { Footer } from '../components/Footer'
import { LoadingDots } from '../components/LoadingDots'
import { NavigationHeader } from '../components/NavigationHeader'
import { QuestionDisplay } from '../components/QuestionDisplay'
import { QuestionInput } from '../components/QuestionInput'
import { UncertainState } from '../components/UncertainState'
import type { ConversationEntry } from '../types/farsight'

type ConversationScreenProps = {
  entries: ConversationEntry[]
  onAsk: (question: string) => void
  onRetry: (entryId: string) => void
  onHome: () => void
}

export function ConversationScreen({
  entries,
  onAsk,
  onRetry,
  onHome,
}: ConversationScreenProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries])

  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader showHomeAction onHome={onHome} />
      <main className="mx-auto flex min-h-[calc(100vh-57px)] max-w-3xl flex-col px-6">
        <div className="flex-1 space-y-10 py-8 sm:py-10">
          {entries.map((entry) => (
            <div key={entry.id} className="space-y-6">
              <QuestionDisplay question={entry.question} />

              {entry.isLoading ? <LoadingDots /> : null}

              {!entry.isLoading && entry.error ? (
                <ErrorState message={entry.error} onRetry={() => onRetry(entry.id)} />
              ) : null}

              {!entry.isLoading && !entry.error && entry.response?.found ? (
                <AnswerCard
                  answer={entry.response.answer}
                  excerpt={entry.response.excerpt}
                  citation={entry.response.citation}
                />
              ) : null}

              {!entry.isLoading && !entry.error && entry.response && !entry.response.found ? (
                <UncertainState message={entry.response.answer} />
              ) : null}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <div className="sticky bottom-0 border-t border-border/60 bg-background/90 py-4 backdrop-blur-lg">
          <QuestionInput
            onSubmit={onAsk}
            disabled={entries.some((e) => e.isLoading)}
            compact
            placeholder="Ask another FAR/AIM question..."
          />
        </div>
      </main>

      <Footer />
    </div>
  )
}
