import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { PileDoc } from '../types'

// Shows every live /pile-analysis working doc of the MTG card-library repo
// (.cycle/*-analysis.md) in a band above the prompt: its title and the
// `**Status: …**` line the skill keeps current. CLAUDE.md names these docs as
// the thing a fresh session must find; this makes them impossible to miss.

const CYCLE = '.cycle'
const docs = atom({ plugin: 'pile-tracker', key: 'docs' } as const, [])
const isHidden = atom({ plugin: 'pile-tracker', key: 'isHidden' } as const, false)

export function parseDoc(file: string, text: string): PileDoc {
  const heading = /^#\s+(.+)$/m.exec(text)?.[1] ?? file
  const title = heading.replace(/\s*[—-]\s*analysis\b.*$/i, '').trim()
  const raw = /\*\*Status:\s*([\s\S]*?)\*\*/.exec(text)?.[1] ?? 'no status line'
  const status = raw.replace(/\s+/g, ' ').trim().replace(/\.$/, '')
  return { file, title, status }
}

async function scan($: EngineInterface): Promise<void> {
  if (!(await $.fs.exists(CYCLE))) {
    await update($, docs, () => [])
    return
  }
  const entries = await $.fs.list(CYCLE)
  const names = entries
    .filter(en => en.kind === 'file' && en.name.endsWith('-analysis.md'))
    .map(en => en.name)
    .sort()
  const found: PileDoc[] = []
  for (const name of names) {
    found.push(parseDoc(name, await $.fs.read(`${CYCLE}/${name}`)))
  }
  await update($, docs, () => found)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'piles',
      description: 'List the live pile-analysis docs and show the pile band again',
    })
    $.clock.after(1, () => void scan($))
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    $.clock.after(1, () => void scan($))
    return done
  })

  on('command.run', { command: 'piles' }, async $ => {
    await scan($)
    await update($, isHidden, () => false)
    const list = await read($, docs)
    if (list.length === 0) return { text: 'No live pile-analysis docs in .cycle/.' }
    return {
      text: list.map(d => `${CYCLE}/${d.file}\n  ${d.title}: ${d.status}`).join('\n'),
    }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const list = await read($, docs)
    if (e.props.hasSurvey || list.length === 0 || (await read($, isHidden))) {
      return next(e)
    }
    const { Box, Button, Text } = $.ui.resolve(e)
    const shown = list.slice(0, 3)
    return (
      <Box flexDirection="column">
        {shown.map(d => (
          <Text wrap="truncate-end">
            <Text bold>Pile · {d.title}</Text>
            <Text dimColor> — {d.status}</Text>
          </Text>
        ))}
        <Box>
          {list.length > shown.length && (
            <Text dimColor>+{list.length - shown.length} more (/piles) </Text>
          )}
          <Button key="hide" label="Hide" onPress={() => update($, isHidden, () => true)} />
        </Box>
      </Box>
    )
  })
}
