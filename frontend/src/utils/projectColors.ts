/**
 * Ready-made project colors. Mid-tones on purpose: they only ever appear as
 * small dots and chips, and have to read on both the light and the dark sheet.
 * `name` is a locale key under `projects.colors`, read out instead of the hex.
 */
export const PROJECT_COLORS = [
  { value: '#3a7bd5', name: 'blue' },
  { value: '#0f8fa8', name: 'cyan' },
  { value: '#2a9d8f', name: 'teal' },
  { value: '#4c9a2a', name: 'green' },
  { value: '#b8862b', name: 'ochre' },
  { value: '#d9822b', name: 'orange' },
  { value: '#c2572c', name: 'rust' },
  { value: '#c23a6b', name: 'raspberry' },
  { value: '#9b4dca', name: 'violet' },
  { value: '#5b5fc7', name: 'indigo' },
  { value: '#8a6a4f', name: 'brown' },
  { value: '#6b7f8e', name: 'slate' },
] as const

/** The first preset nobody uses yet, so a new project stands out from the rest. */
export function nextProjectColor(taken: readonly string[]): string {
  const used = new Set(taken.map((color) => color.toLowerCase()))
  const free = PROJECT_COLORS.find((color) => !used.has(color.value))
  return (free ?? PROJECT_COLORS[taken.length % PROJECT_COLORS.length]!).value
}
