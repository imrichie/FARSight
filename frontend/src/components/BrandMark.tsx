export function BrandMark() {
  return (
    <div className="inline-flex items-center gap-2.5">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary-hover shadow-sm">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            d="M12 2L14.4 9.6L22 12L14.4 14.4L12 22L9.6 14.4L2 12L9.6 9.6L12 2Z"
            fill="white"
            fillOpacity="0.95"
          />
        </svg>
      </div>
      <span className="text-lg font-bold tracking-tight text-foreground">
        FARSight
      </span>
    </div>
  )
}
