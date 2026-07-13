import { BookOpen, Mail } from 'lucide-react'

function GithubIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
    </svg>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-border/60 bg-secondary/30">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <p className="text-xs font-semibold uppercase tracking-wider text-primary">
          Want the full story?
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <a
            href="https://imrichie.github.io/farsight-case-study/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-primary/20 bg-gradient-to-r from-primary/15 to-primary/8 px-4 py-2.5 text-sm font-semibold text-primary shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md active:scale-[0.97]"
          >
            <BookOpen className="h-4 w-4" aria-hidden="true" />
            Read the case study
          </a>
          <a
            href="https://github.com/imrichie/farsight"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-semibold text-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:text-primary active:scale-[0.97]"
          >
            <GithubIcon />
            View the source
          </a>
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
          <span>
            Built by <span className="font-medium text-foreground">Ricardo Flores</span>
          </span>
          <span aria-hidden="true">·</span>
          <a
            href="mailto:rfloresc@icloud.com"
            className="inline-flex items-center gap-1 transition-colors hover:text-primary"
          >
            <Mail className="h-3.5 w-3.5" aria-hidden="true" />
            rfloresc@icloud.com
          </a>
        </div>

        <p className="mt-6 text-xs leading-relaxed text-muted-foreground/70">
          Portfolio demo — not a substitute for official FAA guidance or CFI instruction.
        </p>
      </div>
    </footer>
  )
}
