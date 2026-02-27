/**
 * Empty state — generous vertical breathing room.
 * Icon recedes (very muted), text is the signal.
 */
export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-hover">
          <Icon className="h-5 w-5 text-ink-400" weight="light" />
        </div>
      )}
      <h3 className="text-sm font-semibold text-ink-900 tracking-snug">{title}</h3>
      {description && (
        <p className="mt-1.5 text-sm text-ink-400 max-w-xs leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
