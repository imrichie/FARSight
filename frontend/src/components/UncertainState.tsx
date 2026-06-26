import { motion } from 'motion/react'
import { AlertCircle } from 'lucide-react'

type UncertainStateProps = {
  message: string
}

export function UncertainState({ message }: UncertainStateProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="rounded-2xl border border-amber-200/80 bg-gradient-to-br from-amber-50 to-amber-50/50 p-6 sm:p-8"
      style={{ boxShadow: '0 2px 8px rgba(217, 119, 6, 0.06)' }}
    >
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-600">
          <AlertCircle className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-tight text-foreground">
            I couldn't find a confident answer in the FAR/AIM
          </h2>
          <p className="mt-2.5 text-base leading-relaxed text-muted-foreground">{message}</p>
        </div>
      </div>
    </motion.section>
  )
}
