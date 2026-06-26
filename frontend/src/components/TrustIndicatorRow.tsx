import { BookOpen, CheckCircle2, Sparkles } from 'lucide-react'

const trustIndicators = [
  {
    icon: BookOpen,
    title: 'Official Sources',
    description: 'Every answer cites the exact FAR/AIM section.',
  },
  {
    icon: CheckCircle2,
    title: 'Verified Excerpts',
    description: 'The quoted source text must match the retrieved chunk.',
  },
  {
    icon: Sparkles,
    title: 'Study Smart',
    description: 'Plain-English answers for student-pilot review.',
  },
]

export function TrustIndicatorRow() {
  return (
    <section className="grid gap-6 border-t border-border pt-8 sm:grid-cols-3">
      {trustIndicators.map((indicator) => {
        const Icon = indicator.icon
        return (
          <div key={indicator.title} className="flex gap-3">
            <Icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
            <div>
              <h3 className="font-medium text-foreground">{indicator.title}</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                {indicator.description}
              </p>
            </div>
          </div>
        )
      })}
    </section>
  )
}
