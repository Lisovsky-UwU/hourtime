/**
 * The running timer.
 *
 * The backend owns the truth: this store only mirrors `/time-entries/current`
 * and ticks a local counter derived from `started_at` and the server clock.
 * That is what makes a reload — or a different browser — pick up the same
 * running timer instead of a lost one.
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as entriesApi from '@/api/timeEntries'
import type { TimeEntry } from '@/types'
import { elapsedSeconds } from '@/utils/serverTime'

export const useTimerStore = defineStore('timer', () => {
  const entry = ref<TimeEntry | null>(null)
  const elapsed = ref(0)
  const syncing = ref(false)

  const isRunning = computed(() => entry.value !== null)

  let ticker: number | null = null

  function recomputeElapsed(): void {
    elapsed.value = entry.value ? elapsedSeconds(entry.value.started_at) : 0
  }

  function startTicking(): void {
    recomputeElapsed()
    if (ticker !== null) return
    ticker = window.setInterval(recomputeElapsed, 1000)
  }

  function stopTicking(): void {
    if (ticker !== null) {
      window.clearInterval(ticker)
      ticker = null
    }
    elapsed.value = 0
  }

  function adopt(next: TimeEntry | null): void {
    entry.value = next
    if (next) startTicking()
    else stopTicking()
  }

  /** Re-read the server's running entry. Cheap enough to call on every focus. */
  async function sync(): Promise<void> {
    syncing.value = true
    try {
      adopt(await entriesApi.current())
    } finally {
      syncing.value = false
    }
  }

  async function start(payload: entriesApi.StartPayload = {}): Promise<TimeEntry> {
    const started = await entriesApi.start(payload)
    adopt(started)
    return started
  }

  async function stop(stoppedAt?: string): Promise<TimeEntry | null> {
    const running = entry.value
    if (!running) return null
    const stopped = await entriesApi.stop(running.id, stoppedAt)
    adopt(null)
    return stopped
  }

  /** Re-point the running entry at a different project or comment. */
  async function amend(patch: entriesApi.EntryPatch): Promise<void> {
    const running = entry.value
    if (!running) return
    adopt(await entriesApi.update(running.id, patch))
  }

  /**
   * Seconds tracked by an entry, ticking live for the one that is running.
   *
   * Reading `elapsed` here is what makes the entry list and the day totals
   * update every second instead of freezing at the value they were rendered with.
   */
  function secondsOf(item: TimeEntry): number {
    if (item.duration_seconds !== null) return item.duration_seconds
    if (entry.value?.id === item.id) return elapsed.value
    return elapsedSeconds(item.started_at)
  }

  function reset(): void {
    adopt(null)
  }

  return { entry, elapsed, syncing, isRunning, secondsOf, sync, start, stop, amend, reset }
})
