import { BookOpen } from 'lucide-react'
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

      <div className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(217, 119, 6, 0.07) 0%, transparent 60%), radial-gradient(ellipse 60% 40% at 70% 0%, rgba(12, 74, 110, 0.04) 0%, transparent 50%)',
          }}
        />

        <main className="relative mx-auto flex max-w-3xl flex-col gap-16 px-6 py-16 sm:gap-20 sm:py-24">
          <section className="space-y-10">
            <div className="space-y-6">
              <BrandPill variant="primary">
                <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
                FAR/AIM + AI-powered search
              </BrandPill>
              <div className="space-y-5">
                <h1 className="max-w-2xl text-balance text-4xl font-extrabold leading-[1.1] tracking-tight text-foreground sm:text-5xl md:text-6xl">
                  Ask FAA questions.{' '}
                  <span className="bg-gradient-to-r from-primary to-amber-500 bg-clip-text text-transparent">
                    Get cited answers.
                  </span>
                </h1>
                <p className="max-w-xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
                  FARSight turns private-pilot FAR/AIM questions into plain-English
                  answers with official source excerpts.
                </p>
              </div>
            </div>
            <QuestionInput onSubmit={onAsk} />
          </section>

          <section className="space-y-5">
            <h2 className="text-lg font-bold tracking-tight text-foreground">
              Try a question
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {exampleQuestions.map((question) => (
                <ExampleQuestionCard key={question} question={question} onSelect={onAsk} />
              ))}
            </div>
          </section>
          <div className="border-t border-border/50 pt-14">
            <TrustIndicatorRow />
          </div>
        </main>
      </div>
    </div>
  )
}
