import { motion } from 'motion/react'

export function LoadingDots() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-6 text-muted-foreground shadow-sm">
      <div className="flex gap-2" aria-hidden="true">
        {[0, 1, 2].map((index) => (
          <motion.div
            key={index}
            className="h-2 w-2 rounded-full bg-primary"
            animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.2, 1] }}
            transition={{
              duration: 1.4,
              repeat: Infinity,
              delay: index * 0.2,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>
      <span className="text-base">Searching the FAR/AIM...</span>
    </div>
  )
}
