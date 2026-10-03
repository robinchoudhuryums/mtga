import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { DeckSnapshot } from '../types'

// A live deck dashboard for the MTG card-library repo. `/deck <id>` opens a pane
// showing the deck's tier floor and the numbers behind it, read from the repo's
// own CLI (scripts/deck.py), so the pane can never disagree with the tools. It
// re-reads itself after any command or edit that writes a deck file.

const PANE = 'deck-pane'
const DECK_PY = 'scripts/deck.py'

const deckId = atom({ plugin: 'deck-pane', key: 'deckId' } as const, null)
const snapshot = atom({ plugin: 'deck-pane', key: 'snapshot' } as const, null)
const isLoading = atom({ plugin: 'deck-pane', key: 'isLoading' } as const, false)
const error = atom({ plugin: 'deck-pane', key: 'error' } as const, null)

// Commands and edits that can change a deck file. Matching loosely is fine:
// a false hit costs one extra refresh, a miss leaves the pane stale.
const DECK_WRITE_RE =
  /deck\.py\s+(swap|move|resolve|sync)\b|make\s+postedit|decks\/[^\s]*\.txt|git\s+(checkout|restore|pull|merge)/

async function runDeckPy($: EngineInterface, args: string[]): Promise<string> {
  const ran = await $.process.run(['python3', DECK_PY, ...args], { timeoutMs: 180000 })
  if (ran.exitCode !== 0) {
    const why = (ran.stderr || ran.stdout).trim().split('\n').slice(-1)[0] ?? ''
    throw new Error(`deck.py ${args[0]} failed: ${why}`)
  }
  return ran.stdout
}

export function parseQuality(stdout: string): Record<string, unknown> {
  const line = stdout.split('\n').find(l => l.trimStart().startsWith('{'))
  if (line === undefined) throw new Error('deck.py quality printed no JSON')
  return JSON.parse(line) as Record<string, unknown>
}

export function parseTier(stdout: string): { name: string; claimed: string; floor: string } {
  const head = /deck\s+\S+:\s*(.+)$/m.exec(stdout)
  const claimed = /claimed tier\s*:\s*(\S+)/.exec(stdout)
  const floor = /metrics floor\s*:\s*(\S+)/.exec(stdout)
  return {
    name: head?.[1]?.trim() ?? '?',
    claimed: claimed?.[1] ?? '—',
    floor: floor?.[1] ?? '?',
  }
}

export function parseConsistency(stdout: string): {
  sources: string
  keepable: string
  worst: string[]
} {
  const keepable = /keepable \(2.5 lands\)\s*:\s*([\d.]+%)/.exec(stdout)?.[1] ?? '?'
  const sources = /^\s+((?:[WUBRGC] \d+\s*)+)$/m.exec(stdout)?.[1]?.trim() ?? '?'
  const worst: string[] = []
  const rowRe = /^\s+([\d.]+%)\s+(T\d+)\s+(\S+)\s+(.+?)\s{2,}/gm
  for (let m = rowRe.exec(stdout); m !== null && worst.length < 3; m = rowRe.exec(stdout)) {
    worst.push(`${m[1]}  ${m[2]}  ${m[4]}  ${m[3]}`)
  }
  return { sources, keepable, worst }
}

async function collect($: EngineInterface, id: string): Promise<DeckSnapshot> {
  const [quality, tier, consistency] = await Promise.all([
    runDeckPy($, ['quality', id, '--json']),
    runDeckPy($, ['tier', id]),
    runDeckPy($, ['consistency', id]),
  ])
  const q = parseQuality(quality)
  const t = parseTier(tier)
  const c = parseConsistency(consistency)
  const num = (k: string): number => (typeof q[k] === 'number' ? (q[k] as number) : 0)
  const str = (k: string, fallback: string): string =>
    typeof q[k] === 'string' ? (q[k] as string) : fallback
  return {
    id,
    name: t.name,
    claimed: t.claimed,
    floor: t.floor,
    plan: str('plan', '?'),
    interaction: str('interaction_conf', String(num('interaction'))),
    cardAdvantage: str('card_advantage_conf', String(num('card_advantage'))),
    protection: num('protection'),
    boardPower: num('board_power'),
    avgMv: num('avg_mv'),
    earlyDrops: num('early_drops'),
    buildable: q.buildable === true,
    missing: num('missing'),
    short: num('short'),
    sources: c.sources,
    keepable: c.keepable,
    worst: c.worst,
    refreshedAt: await $.clock.now(),
  }
}

// Re-reads the deck and stores the result; resolves to the snapshot, or to the
// error text when deck.py failed, so a command can answer with either.
async function refresh($: EngineInterface): Promise<DeckSnapshot | string | null> {
  const id = await read($, deckId)
  if (id === null) return null
  await update($, isLoading, () => true)
  try {
    const snap = await collect($, id)
    await update($, snapshot, () => snap)
    await update($, error, () => null)
    return snap
  } catch (err) {
    const why = err instanceof Error ? err.message : String(err)
    await update($, error, () => why)
    return why
  } finally {
    await update($, isLoading, () => false)
  }
}

// The same numbers the pane draws, as plain text, for the command's reply: a
// client that draws no panes (the mobile and web views of a cloud session)
// still gets the dashboard.
export function formatSnapshot(snap: DeckSnapshot): string {
  const build = snap.buildable
    ? 'buildable from owned cards'
    : `${snap.missing} missing, ${snap.short} short`
  const lines = [
    `Deck ${snap.id} · ${snap.name}`,
    `Tier ${snap.claimed} · floor ${snap.floor} (${snap.plan})`,
    `Interaction ${snap.interaction} · card advantage ${snap.cardAdvantage}`,
    `Protection ${snap.protection} · board power ${snap.boardPower}`,
    `Avg MV ${snap.avgMv.toFixed(2)} · early drops ${snap.earlyDrops}`,
    `Sources ${snap.sources} · keepable ${snap.keepable}`,
    'Weakest on curve:',
    ...(snap.worst.length === 0 ? ['  (none listed)'] : snap.worst.map(row => `  ${row}`)),
    `Build: ${build}`,
  ]
  return lines.join('\n')
}

function clock(ms: number): string {
  const d = new Date(ms)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'deck',
      description: 'Open a live dashboard pane for one deck (tier floor, axes, mana, buildability)',
      argumentHint: '<deck id>',
    })
    return next(e)
  })

  on('command.run', { command: 'deck' }, async ($, e) => {
    const asked = e.args.trim().split(/\s+/)[0] ?? ''
    const id = asked !== '' ? asked : await read($, deckId)
    if (id === null || id === '') {
      return { text: 'Usage: /deck <deck id>, e.g. /deck 81' }
    }
    if (!(await $.fs.exists(DECK_PY))) {
      return { text: `deck-pane: ${DECK_PY} not found — run Claude Code from the card-library repo root.` }
    }
    if (id !== (await read($, deckId))) {
      await update($, snapshot, () => null)
    }
    await update($, deckId, () => id)
    await $.ui.open({ id: PANE, title: `Deck ${id}` })
    const got = await refresh($)
    if (got === null) return { text: 'Usage: /deck <deck id>, e.g. /deck 81' }
    if (typeof got === 'string') return { text: `deck-pane: ${got}` }
    return { text: `${formatSnapshot(got)}\n(The pane, where your client draws one, refreshes after deck edits.)` }
  })

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if ((await read($, deckId)) === null) return ran
    let touched = false
    if (e.tool === 'Bash') touched = DECK_WRITE_RE.test(e.command)
    else if (e.tool === 'Edit' || e.tool === 'Write') touched = /(^|\/)decks\//.test(e.file_path)
    if (touched) $.clock.after(1, () => void refresh($))
    return ran
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const id = await read($, deckId)
    const snap = await read($, snapshot)
    const loading = await read($, isLoading)
    const err = await read($, error)

    if (id === null) {
      return <Text dimColor>No deck selected. Run /deck &lt;id&gt;.</Text>
    }
    if (snap === null) {
      return (
        <Box flexDirection="column">
          <Text dimColor>{loading ? `Reading deck ${id}…` : `Deck ${id}: no data yet.`}</Text>
          {err !== null && <Text color="red">{err}</Text>}
        </Box>
      )
    }

    const tierOk = snap.claimed === snap.floor
    return (
      <Box flexDirection="column">
        <Text bold wrap="truncate-end">
          {snap.id} · {snap.name}
        </Text>
        <Text color={tierOk ? 'green' : 'yellow'}>
          Tier {snap.claimed} · floor {snap.floor} ({snap.plan})
        </Text>
        <Text>Interaction {snap.interaction}</Text>
        <Text>Card advantage {snap.cardAdvantage}</Text>
        <Text>
          Protection {snap.protection} · Board power {snap.boardPower}
        </Text>
        <Text>
          Avg MV {snap.avgMv.toFixed(2)} · Early drops {snap.earlyDrops}
        </Text>
        <Text>
          Sources {snap.sources} · Keepable {snap.keepable}
        </Text>
        <Text bold>Weakest on curve</Text>
        {snap.worst.length === 0 && <Text dimColor>  (none listed)</Text>}
        {snap.worst.map(row => (
          <Text wrap="truncate-end">  {row}</Text>
        ))}
        <Text color={snap.buildable ? 'green' : 'yellow'}>
          {snap.buildable ? 'Buildable from owned cards' : `${snap.missing} missing, ${snap.short} short`}
        </Text>
        {err !== null && <Text color="red">{err}</Text>}
        <Box>
          <Text dimColor>
            {loading ? 'refreshing… ' : `as of ${clock(snap.refreshedAt)} `}
          </Text>
          <Button key="refresh" label="Refresh" hotkey="r" onPress={() => void refresh($)} />
        </Box>
      </Box>
    )
  })
}
