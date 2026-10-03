export type DeckSnapshot = {
  id: string
  name: string
  claimed: string
  floor: string
  plan: string
  interaction: string
  cardAdvantage: string
  protection: number
  boardPower: number
  avgMv: number
  earlyDrops: number
  buildable: boolean
  missing: number
  short: number
  sources: string
  keepable: string
  worst: string[]
  refreshedAt: number
}

declare module 'claude-code' {
  interface PluginState {
    'deck-pane': {
      deckId: string | null
      snapshot: DeckSnapshot | null
      isLoading: boolean
      error: string | null
    }
  }
}
