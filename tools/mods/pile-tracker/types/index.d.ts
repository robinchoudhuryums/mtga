export type PileDoc = { file: string; title: string; status: string }

declare module 'claude-code' {
  interface PluginState {
    'pile-tracker': { docs: PileDoc[]; isHidden: boolean }
  }
}
