import { Sparkles } from 'lucide-react'
import { BrandPill } from '../components/BrandPill'
import { ExampleQuestionCard } from '../components/ExampleQuestionCard'
import { NavigationHeader } from '../components/NavigationHeader'
import { QuestionInput } from '../components/QuestionInput'
import { TrustIndicatorRow } from '../components/TrustIndicatorRow'
import { exampleQuestions } from '../data/exampleQuestions'

type HomeScreenProps = {
  onAsk: (question: string) => void
}

export function HomeScreen({ onAsk }: HomeScreenProps) {
  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader />
      <main className="mx-auto flex max-w-4xl flex-col gap-12 px-6 py-12 sm:gap-16 sm:py-16">
        <section className="space-y-8">
          <div className="space-y-6">
            <BrandPill variant="primary">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Powered by FAR/AIM
            </BrandPill>
            <div className="space-y-5">
              <h1 className="max-w-3xl text-5xl font-semibold leading-tight text-foreground sm:text-6xl">
                Ask FAA questions. Get cited answers.
              </h1>
              <p className="max-w-2xl text-xl leading-relaxed text-muted-foreground">
                FARSight turns private-pilot FAR/AIM questions into plain-English
                answers with official source excerpts.
              </p>
            </div>
          </div>
          <QuestionInput onSubmit={onAsk} />
        </section>

        <section className="space-y-4">
          <p className="text-sm font-medium text-muted-foreground">Popular questions</p>
          <div className="grid gap-4 sm:grid-cols-2">
            {exampleQuestions.map((question) => (
              <ExampleQuestionCard key={question} question={question} onSelect={onAsk} />
            ))}
          </div>
        </section>

        <TrustIndicatorRow />
      </main>
    </div>
  )
}
