import { describe, expect, test } from 'claude-code/testing'

import { formatSnapshot } from '../hooks/register'

const SNAP = {
  id: '81',
  name: 'Heartwood Foundry (RG artifact tokens + Dragon forge)',
  claimed: 'A',
  floor: 'A',
  plan: 'midrange',
  interaction: '12',
  cardAdvantage: '4',
  protection: 2,
  boardPower: 66,
  avgMv: 3.42,
  earlyDrops: 13,
  buildable: false,
  missing: 20,
  short: 0,
  sources: 'R 17   G 17',
  keepable: '84.4%',
  worst: ['66.4%  T5  Craterclaw Colossus  {R}{R}{R}'],
  refreshedAt: 0,
}

describe('deck-pane text reply', () => {
  test('carries the same numbers the pane draws', async () => {
    const text = formatSnapshot(SNAP)
    expect(text).toContain('Deck 81 · Heartwood Foundry')
    expect(text).toContain('Tier A · floor A (midrange)')
    expect(text).toContain('Interaction 12 · card advantage 4')
    expect(text).toContain('Avg MV 3.42')
    expect(text).toContain('Sources R 17   G 17 · keepable 84.4%')
    expect(text).toContain('  66.4%  T5  Craterclaw Colossus')
    expect(text).toContain('Build: 20 missing, 0 short')
  })

  test('says so when nothing is weak on curve, and when the deck is owned', async () => {
    const text = formatSnapshot({ ...SNAP, worst: [], buildable: true })
    expect(text).toContain('(none listed)')
    expect(text).toContain('Build: buildable from owned cards')
  })
})
