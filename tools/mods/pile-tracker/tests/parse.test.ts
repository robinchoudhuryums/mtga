import { describe, expect, test } from 'claude-code/testing'

import { parseDoc } from '../hooks/register'

const DOC = `# FRA BUR pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — black-red build DRAFTED 2026-10-03 as deck 81 (Detention Hall); the
blue-black Theorist variant and the UR Saheeli idea are still open.** Delete once the deck(s) land.
`

describe('pile-tracker parseDoc', () => {
  test('title drops the boilerplate, status joins wrapped lines', async () => {
    const d = parseDoc('fra-bur-pile-analysis.md', DOC)
    expect(d.title).toBe('FRA BUR pile')
    expect(d.status).toBe(
      'IN PROGRESS — black-red build DRAFTED 2026-10-03 as deck 81 (Detention Hall); the blue-black Theorist variant and the UR Saheeli idea are still open',
    )
  })

  test('a doc with no status line says so', async () => {
    expect(parseDoc('x-analysis.md', '# X pile — analysis\n').status).toBe('no status line')
  })
})
