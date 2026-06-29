import { useState } from 'react'
import { askFarsight, ApiError } from './data/api'
import { ConversationScreen } from './screens/ConversationScreen'
import { HomeScreen } from './screens/HomeScreen'
import type { ConversationEntry } from './types/farsight'

export function App() {
  const [entries, setEntries] = useState<ConversationEntry[]>([])

  async function askQuestion(question: string) {
    const id = crypto.randomUUID()
    const newEntry: ConversationEntry = {
      id,
      question,
      response: null,
      isLoading: true,
      error: null,
    }

    setEntries((previous) => [...previous, newEntry])

    try {
      const response = await askFarsight(question)
      setEntries((previous) =>
        previous.map((entry) =>
          entry.id === id ? { ...entry, response, isLoading: false } : entry,
        ),
      )
    } catch (caught) {
      const message =
        caught instanceof ApiError
          ? caught.message
          : 'Having trouble reaching the regulations right now. Please try again in a moment.'
      setEntries((previous) =>
        previous.map((entry) =>
          entry.id === id ? { ...entry, error: message, isLoading: false } : entry,
        ),
      )
    }
  }

  function retryQuestion(entryId: string) {
    const entry = entries.find((e) => e.id === entryId)
    if (!entry) return

    setEntries((previous) => previous.filter((e) => e.id !== entryId))
    askQuestion(entry.question)
  }

  function returnHome() {
    setEntries([])
  }

  if (entries.length === 0) {
    return <HomeScreen onAsk={askQuestion} />
  }

  return (
    <ConversationScreen
      entries={entries}
      onAsk={askQuestion}
      onRetry={retryQuestion}
      onHome={returnHome}
    />
  )
}
