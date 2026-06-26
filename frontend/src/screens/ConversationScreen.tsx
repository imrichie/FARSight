import { AnswerCard } from '../components/AnswerCard'
import { LoadingDots } from '../components/LoadingDots'
import { NavigationHeader } from '../components/NavigationHeader'
import { QuestionDisplay } from '../components/QuestionDisplay'
import { QuestionInput } from '../components/QuestionInput'
import { UncertainState } from '../components/UncertainState'
import type { MockFarsightResponse } from '../types/farsight'

type ConversationScreenProps = {
  question: string
  response: MockFarsightResponse | null
  isLoading: boolean
  onAsk: (question: string) => void
  onHome: () => void
}

export function ConversationScreen({
  question,
  response,
  isLoading,
  onAsk,
  onHome,
}: ConversationScreenProps) {
  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader showHomeAction onHome={onHome} />
      <main className="mx-auto flex min-h-[calc(100vh-73px)] max-w-4xl flex-col px-6">
        <div className="flex-1 space-y-8 py-8 sm:py-10">
          <QuestionDisplay question={question} />

          {isLoading ? <LoadingDots /> : null}

          {!isLoading && response?.found ? (
            <AnswerCard
              answer={response.answer}
              excerpt={response.excerpt}
              citation={response.citation}
            />
          ) : null}

          {!isLoading && response && !response.found ? (
            <UncertainState message={response.answer} />
          ) : null}
        </div>

        <div className="sticky bottom-0 border-t border-border bg-background/95 py-4 backdrop-blur">
          <QuestionInput
            onSubmit={onAsk}
            disabled={isLoading}
            compact
            placeholder="Ask another FAR/AIM question..."
          />
        </div>
      </main>
    </div>
  )
}
