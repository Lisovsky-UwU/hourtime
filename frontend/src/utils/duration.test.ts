import assert from 'node:assert/strict'
import test from 'node:test'

import { parseDurationText } from './duration.ts'

test('parseDurationText', () => {
  assert.equal(parseDurationText(''), 0)
  assert.equal(parseDurationText('1:30'), 5400)
  assert.equal(parseDurationText('1:30:15'), 5415)
  assert.equal(parseDurationText('1,5'), 5400)
  assert.equal(parseDurationText('2'), 7200)
  // An estimate has no day cap.
  assert.equal(parseDurationText('40'), 144_000)
  assert.equal(parseDurationText('40:00'), 144_000)
  assert.equal(parseDurationText('0:75'), null)
  assert.equal(parseDurationText('abc'), null)
})
