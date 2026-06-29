import { motion } from 'motion/react'
import { WifiOff } from 'lucide-react'

type ErrorStateProps = {
  message: string
  onRetry: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="rounded-2xl border border-red-200/80 bg-gradient-to-br from-red-50 to-red-50/50 p-6 sm:p-8"
      style={{ boxShadow: '0 2px 8px rgba(220, 38, 38, 0.06)' }}
    >
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-100 text-red-500">
          <WifiOff className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-tight text-foreground">
            Couldn't reach the regulations
          </h2>
          <p className="mt-2.5 text-base leading-relaxed text-muted-foreground">{message}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 inline-flex items-center rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-foreground shadow-sm transition-all hover:bg-primary/10 hover:text-primary hover:shadow-md active:scale-[0.97]"
          >
            Try again
          </button>
        </div>
      </div>
    </motion.section>
  )
}
