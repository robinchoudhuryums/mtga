import { expect, test } from 'claude-code/testing'

const BAND = {
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 4,
    bodyColumns: 80,
    scroll: { offset: 0, bodyRows: 4 },
    view: {},
  },
} as const

test('with no analysis docs the band draws nothing of its own', async ($, on) => {
  // Stands in for the engine beneath the plugin: what it draws when the band passes.
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text key="engine">engine band</Text>
  })
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ plugin: 'pile-tracker', surface, ...BAND })
    expect(await ui.find({ key: 'hide' })).toBeUndefined()
    await ui.unmount()
  }
})
