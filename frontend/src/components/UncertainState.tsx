import { AlertCircle } from 'lucide-react'

type UncertainStateProps = {
  message: string
}

export function UncertainState({ message }: UncertainStateProps) {
  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-6 sm:p-8">
      <div className="flex flex-col gap-5 sm:flex-row">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-600">
          <AlertCircle className="h-6 w-6" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            I couldn't find a confident answer in the FAR/AIM
          </h2>
          <p className="mt-3 text-lg leading-relaxed text-muted-foreground">{message}</p>
        </div>
      </div>
    </section>
  )
}
