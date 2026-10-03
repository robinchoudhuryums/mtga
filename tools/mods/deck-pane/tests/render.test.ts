import { expect, test } from 'claude-code/testing'

const PANE = {
  component: 'Pane',
  requestId: 'deck-pane',
  props: {
    title: 'Deck',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

test('with no deck chosen the pane says how to pick one', async $ => {
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ plugin: 'deck-pane', surface, ...PANE })
    expect(await ui.find({ type: 'Text', text: /\/deck/ })).toBeDefined()
    await ui.unmount()
  }
})
