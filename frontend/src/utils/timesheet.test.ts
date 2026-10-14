// Run with `npm test` (Node's own runner; Node strips the types).
import assert from 'node:assert/strict'
import { test } from 'node:test'

import { parseDuration, planCellChange } from './timesheet.ts'

test('parseDuration', () => {
  assert.equal(parseDuration(''), 0)
  assert.equal(parseDuration('1:30'), 5400)
  assert.equal(parseDuration('1:30:15'), 5415)
  assert.equal(parseDuration('1,5'), 5400)
  assert.equal(parseDuration('2'), 7200)
  assert.equal(parseDuration('0:75'), null)
  assert.equal(parseDuration('25'), null)
  assert.equal(parseDuration('abc'), null)
})

test('planCellChange', () => {
  const H = 3_600_000
  const day0 = Date.parse('2026-10-12T00:00:00Z')
  const iso = (ms: number) => new Date(ms).toISOString()
  const e = (id: string, from: number, to: number) => ({
    id,
    started_at: iso(day0 + from * H),
    stopped_at: iso(day0 + to * H),
  })
  const far = day0 + 100 * H

  // empty day -> 09:00
  assert.deepEqual(
    planCellChange([], 2 * 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: null,
      now: far,
    }),
    [{ kind: 'create', startedAt: day0 + 9 * H, stoppedAt: day0 + 11 * H }],
  )
  // after last end
  assert.deepEqual(
    planCellChange([e('a', 9, 10)], 3 * 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: day0 + 12 * H,
      now: far,
    }),
    [{ kind: 'create', startedAt: day0 + 12 * H, stoppedAt: day0 + 14 * H }],
  )
  // would end in future -> ends now
  assert.deepEqual(
    planCellChange([], 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: day0 + 9 * H,
      now: day0 + 9.5 * H,
    }),
    [{ kind: 'create', startedAt: day0 + 8.5 * H, stoppedAt: day0 + 9.5 * H }],
  )
  // last entry ran past midnight -> ends at midnight
  assert.deepEqual(
    planCellChange([], 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: day0 + 25 * H,
      now: far,
    }),
    [{ kind: 'create', startedAt: day0 + 23 * H, stoppedAt: day0 + 24 * H }],
  )
  // no room
  assert.equal(
    planCellChange([], 3 * 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: null,
      now: day0 + 2 * H,
    }),
    null,
  )
  // unchanged
  assert.deepEqual(
    planCellChange([e('a', 9, 10)], 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: null,
      now: far,
    }),
    [],
  )
  // shorten latest
  assert.deepEqual(
    planCellChange([e('a', 9, 10), e('b', 11, 13)], 2 * 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: null,
      now: far,
    }),
    [{ kind: 'shorten', id: 'b', stoppedAt: day0 + 12 * H }],
  )
  // delete latest + shorten previous
  assert.deepEqual(
    planCellChange([e('b', 11, 12), e('a', 9, 11)], 1800, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: null,
      now: far,
    }),
    [
      { kind: 'delete', id: 'b' },
      { kind: 'shorten', id: 'a', stoppedAt: day0 + 9.5 * H },
    ],
  )
  // exact delete
  assert.deepEqual(
    planCellChange([e('a', 9, 10), e('b', 11, 12)], 3600, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: null,
      now: far,
    }),
    [{ kind: 'delete', id: 'b' }],
  )
  // zero deletes all
  assert.deepEqual(
    planCellChange([e('a', 9, 10), e('b', 11, 12)], 0, {
      dayStart: day0,
      dayEnd: day0 + 24 * H,
      lastEnd: null,
      now: far,
    }),
    [
      { kind: 'delete', id: 'b' },
      { kind: 'delete', id: 'a' },
    ],
  )
})
