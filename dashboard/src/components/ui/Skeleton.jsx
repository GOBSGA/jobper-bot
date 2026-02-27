/**
 * Skeleton loaders — replace spinners for content-aware loading states.
 * animate-pulse with surface-border color gives the "shimmer" effect.
 */

export default function Skeleton({ className = "" }) {
  return (
    <div className={`animate-pulse bg-surface-border rounded-lg ${className}`} />
  );
}

/** Multiple lines of text skeleton */
export function SkeletonText({ lines = 3, className = "" }) {
  const widths = ["w-full", "w-4/5", "w-3/5", "w-full", "w-2/3"];
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={`animate-pulse bg-surface-border rounded h-3 ${widths[i % widths.length]}`}
        />
      ))}
    </div>
  );
}

/** Contract card skeleton — mirrors ContractCard visual structure */
export function SkeletonContractCard() {
  return (
    <div className="bg-white rounded-2xl border border-surface-border p-4 space-y-3">
      {/* Title row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="animate-pulse bg-surface-border rounded h-4 w-3/4" />
          <div className="animate-pulse bg-surface-border rounded h-3 w-1/3" />
        </div>
        <div className="space-y-1 text-right flex-shrink-0">
          <div className="animate-pulse bg-surface-border rounded h-4 w-20" />
          <div className="animate-pulse bg-surface-border rounded h-3 w-16" />
        </div>
      </div>
      {/* Description */}
      <div className="space-y-2">
        <div className="animate-pulse bg-surface-border rounded h-3 w-full" />
        <div className="animate-pulse bg-surface-border rounded h-3 w-5/6" />
      </div>
    </div>
  );
}

/** Marketplace card skeleton */
export function SkeletonMarketplaceCard() {
  return (
    <div className="bg-white rounded-2xl border border-surface-border p-5 space-y-3">
      {/* Title */}
      <div className="animate-pulse bg-surface-border rounded h-4 w-3/4" />
      {/* Badges row */}
      <div className="flex gap-2">
        <div className="animate-pulse bg-surface-border rounded-full h-5 w-16" />
        <div className="animate-pulse bg-surface-border rounded-full h-5 w-12" />
      </div>
      {/* Description */}
      <div className="space-y-2">
        <div className="animate-pulse bg-surface-border rounded h-3 w-full" />
        <div className="animate-pulse bg-surface-border rounded h-3 w-4/5" />
      </div>
      {/* Budget */}
      <div className="animate-pulse bg-surface-border rounded h-5 w-28" />
      {/* Footer */}
      <div className="border-t border-surface-border pt-3 flex justify-between">
        <div className="animate-pulse bg-surface-border rounded h-3 w-24" />
        <div className="animate-pulse bg-surface-border rounded-lg h-7 w-20" />
      </div>
    </div>
  );
}
