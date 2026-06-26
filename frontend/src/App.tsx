import { useState } from 'react'
import { queryMockFarsight } from './data/mockResponses'
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
    }

    setEntries((previous) => [...previous, newEntry])

    const mockResponse = await queryMockFarsight(question)

    setEntries((previous) =>
      previous.map((entry) =>
        entry.id === id ? { ...entry, response: mockResponse, isLoading: false } : entry,
      ),
    )
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
      onHome={returnHome}
    />
  )
}
