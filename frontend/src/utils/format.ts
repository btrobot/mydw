/**
 * Format a byte count into a human-readable size string.
 * e.g. 1048576 -> "1.0 MB"
 */
export function formatSize(bytes: number | null): string {
  if (!bytes) return '—'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

/**
 * Format a duration in seconds into mm:ss string.
 * e.g. 125 -> "2:05"
 */
export function formatDuration(seconds: number | null): string {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}
