import { describe, expect, test } from 'claude-code/testing'

import { parseConsistency, parseQuality, parseTier } from '../hooks/register'

const TIER = `Tier — deck 81: Detention Hall (Rakdos superfriends-aristocrats)
  claimed tier  : A
  metrics floor : A   (measurable-only — blind to bombs/meta, so it under-rates)
  plan          : midrange  (floor weights interaction + card advantage)
`

const CONSISTENCY = `  keepable (2–5 lands) :  84.4%
Color sources (lands producing each color):
  B 19   R 17
   77.6%  T3  {B}{R}{R}  Ingris Stingerquill              → want 23 R sources (have 17, +6)
   84.7%  T4  {R}{R}     Chandra, Torch of Defiance       → want 20 R sources (have 17, +3)
   85.3%  T3  {B}{B}     Ral Zarek, Guest Lecturer        → want 22 B sources (have 19, +3)
   85.3%  T3  {B}{B}     Phyrexian Arena                  → want 22 B sources (have 19, +3)
`

describe('deck-pane parsers', () => {
  test('tier: name, claimed letter and floor', async () => {
    expect(parseTier(TIER)).toEqual({
      name: 'Detention Hall (Rakdos superfriends-aristocrats)',
      claimed: 'A',
      floor: 'A',
    })
  })

  test('consistency: sources, keepable and the three weakest cards', async () => {
    const c = parseConsistency(CONSISTENCY)
    expect(c.sources).toBe('B 19   R 17')
    expect(c.keepable).toBe('84.4%')
    expect(c.worst.length).toBe(3)
    expect(c.worst[0]).toBe('77.6%  T3  Ingris Stingerquill  {B}{R}{R}')
  })

  test('quality: the JSON line is found and parsed', async () => {
    const q = parseQuality('{"interaction": 15, "card_advantage": 6, "plan": "midrange"}\n')
    expect(q.interaction).toBe(15)
    expect(q.plan).toBe('midrange')
  })
})
