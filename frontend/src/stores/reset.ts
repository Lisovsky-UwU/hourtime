import { useClientsStore } from '@/stores/clients'
import { useEntriesStore } from '@/stores/entries'
import { useProjectsStore } from '@/stores/projects'
import { useTagsStore } from '@/stores/tags'
import { useTimerStore } from '@/stores/timer'

/** Forget everything loaded for the signed-in account, so the next one starts clean. */
export function resetAccountData(): void {
  useTimerStore().reset()
  useProjectsStore().reset()
  useClientsStore().reset()
  useTagsStore().reset()
  useEntriesStore().reset()
}
