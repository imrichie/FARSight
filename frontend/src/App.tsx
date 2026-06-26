import { useState } from 'react'
import { queryMockFarsight } from './data/mockResponses'
import { ConversationScreen } from './screens/ConversationScreen'
import { HomeScreen } from './screens/HomeScreen'
import type { MockFarsightResponse } from './types/farsight'

export function App() {
  const [activeQuestion, setActiveQuestion] = useState('')
  const [response, setResponse] = useState<MockFarsightResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  async function askQuestion(question: string) {
    setActiveQuestion(question)
    setResponse(null)
    setIsLoading(true)

    const mockResponse = await queryMockFarsight(question)
    setResponse(mockResponse)
    setIsLoading(false)
  }

  function returnHome() {
    setActiveQuestion('')
    setResponse(null)
    setIsLoading(false)
  }

  if (!activeQuestion) {
    return <HomeScreen onAsk={askQuestion} />
  }

  return (
    <ConversationScreen
      question={activeQuestion}
      response={response}
      isLoading={isLoading}
      onAsk={askQuestion}
      onHome={returnHome}
    />
  )
}
