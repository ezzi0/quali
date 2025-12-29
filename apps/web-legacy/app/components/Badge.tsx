'use client'

export function Badge({ text, color }: { text: string; color?: string }) {
  const tone = color || '#3b82f6'
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '0.15rem 0.5rem',
        borderRadius: '999px',
        fontSize: '0.75rem',
        fontWeight: 700,
        background: `${tone}15`,
        color: tone,
        border: `1px solid ${tone}33`,
      }}
    >
      {text}
    </span>
  )
}
