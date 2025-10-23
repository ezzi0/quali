'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
  tool_calls?: Array<{
    tool: string
    result: any
  }>
}

interface AgentContext {
  conversation_history: any[]
  collected_data: Record<string, any>
  tool_call_count: number
  lead_id?: number
  session_id?: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState<AgentContext | null>(null)
  const [sessionId, setSessionId] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Create or resume session on mount
    initializeSession()
  }, [])

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const initializeSession = async () => {
    try {
      // Check localStorage for existing session
      const storedSessionId = localStorage.getItem('quali_session_id')
      const storedEmail = localStorage.getItem('quali_email')
      const storedPhone = localStorage.getItem('quali_phone')
      
      // Try to recover session by email/phone, or use stored session ID
      const response = await fetch(`${API_BASE}/agent/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: storedEmail,
          phone: storedPhone
        })
      })
      const data = await response.json()
      
      setSessionId(data.session_id)
      setContext(data.context)
      
      // Store session ID in localStorage
      localStorage.setItem('quali_session_id', data.session_id)
      
      // If session was resumed, show the conversation history
      if (data.resumed && data.context?.conversation_history) {
        const history: Message[] = []
        for (const msg of data.context.conversation_history) {
          if (msg.role === 'user' || msg.role === 'assistant') {
            if (msg.content) {
              history.push({
                role: msg.role as 'user' | 'assistant',
                content: msg.content
              })
            }
          }
        }
        setMessages(history)
        console.log('✅ Session resumed with', history.length, 'messages')
      }
    } catch (error) {
      console.error('Failed to initialize session:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      // No timeout for development - let the request complete naturally
      // In production, you may want to add a longer timeout (e.g., 300000ms = 5 minutes)
      const response = await fetch(`${API_BASE}/agent/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
          context: context
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('API error:', response.status, errorText)
        throw new Error(`API error: ${response.status}`)
      }

      if (!response.body) {
        throw new Error('No response body')
      }

      // Process SSE stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let assistantMessage = ''
      let currentToolCalls: Array<{ tool: string, result: any }> = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              // Stream complete - message already added during streaming
              continue
            }

            try {
              const event = JSON.parse(data)

              if (event.type === 'text') {
                assistantMessage += event.content
                // Update assistant message in real-time
                setMessages(prev => {
                  const newMessages = [...prev]
                  const lastMessage = newMessages[newMessages.length - 1]
                  
                  if (lastMessage && lastMessage.role === 'assistant') {
                    // Update existing message
                    lastMessage.content = assistantMessage
                  } else {
                    // Add new assistant message
                    newMessages.push({ role: 'assistant', content: assistantMessage })
                  }
                  
                  return newMessages
                })
              } else if (event.type === 'tool_start') {
                // Tool call started
                console.log('Tool started:', event.tool)
              } else if (event.type === 'tool_result') {
                // Add tool call to current message
                currentToolCalls.push({
                  tool: event.tool,
                  result: event.result
                })
              } else if (event.type === 'context_update') {
                // Update context
                setContext(event.context)
                
                // Check if email or phone was captured and store in localStorage
                const collected = event.context?.collected_data || {}
                if (collected.email) {
                  localStorage.setItem('quali_email', collected.email)
                }
                if (collected.phone) {
                  localStorage.setItem('quali_phone', collected.phone)
                }
              } else if (event.type === 'escalate') {
                // Human needed
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: '🔔 This conversation needs human attention. A specialist will follow up with you soon.'
                }])
              } else if (event.type === 'complete') {
                // Qualification complete
                console.log('Qualification complete:', event.qualification)
              } else if (event.type === 'error') {
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: `Error: ${event.message}`
                }])
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#f9fafb' }}>
      {/* Header */}
      <header style={{
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '1rem 2rem',
      }}>
        <div style={{
          maxWidth: '900px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Link href="/" style={{ color: '#3b82f6', fontWeight: '600' }}>
              ← Back to Leads
            </Link>
            <h1 style={{ fontSize: '1.25rem', fontWeight: '700' }}>
              AI Qualification Agent
            </h1>
          </div>
          {sessionId && (
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
              Session: {sessionId.slice(0, 8)}...
            </div>
          )}
        </div>
      </header>

      {/* Chat Area */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        maxWidth: '900px',
        width: '100%',
        margin: '0 auto',
        padding: '2rem',
      }}>
        {messages.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '4rem 2rem',
            color: '#6b7280',
          }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>👋</div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              Welcome to AI Lead Qualification
            </h2>
            <p>Tell me what kind of property you're looking for and I'll help you find the perfect match!</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                marginBottom: '1.5rem',
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div style={{
                maxWidth: '70%',
                padding: '1rem',
                borderRadius: '12px',
                background: msg.role === 'user' ? '#3b82f6' : 'white',
                color: msg.role === 'user' ? 'white' : '#1f2937',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              }}>
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {msg.content}
                </div>
                
                {/* Tool calls */}
                {msg.tool_calls && msg.tool_calls.length > 0 && (
                  <div style={{
                    marginTop: '0.75rem',
                    paddingTop: '0.75rem',
                    borderTop: '1px solid #e5e7eb',
                  }}>
                    {msg.tool_calls.map((tc, i) => (
                      <div
                        key={i}
                        style={{
                          fontSize: '0.875rem',
                          padding: '0.5rem',
                          background: '#f3f4f6',
                          borderRadius: '6px',
                          marginBottom: '0.5rem',
                        }}
                      >
                        <div style={{ fontWeight: '600', color: '#3b82f6' }}>
                          🔧 {tc.tool}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                          {Array.isArray(tc.result) 
                            ? `Found ${tc.result.length} results`
                            : JSON.stringify(tc.result).slice(0, 100)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {loading && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: '1.5rem',
          }}>
            <div style={{
              padding: '1rem',
              borderRadius: '12px',
              background: 'white',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        background: 'white',
        borderTop: '1px solid #e5e7eb',
        padding: '1.5rem',
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Tell me what you're looking for..."
              disabled={loading}
              rows={2}
              style={{
                flex: 1,
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '1rem',
                resize: 'none',
                fontFamily: 'inherit',
              }}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              style={{
                padding: '0.75rem 2rem',
                background: loading || !input.trim() ? '#d1d5db' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              }}
            >
              Send
            </button>
          </div>
          
          {context && context.tool_call_count > 0 && (
            <div style={{
              marginTop: '0.75rem',
              fontSize: '0.75rem',
              color: '#6b7280',
              display: 'flex',
              justifyContent: 'space-between',
            }}>
              <span>Tool calls: {context.tool_call_count}/10</span>
              {Object.keys(context.collected_data).length > 0 && (
                <span>Data collected: {Object.keys(context.collected_data).length} fields</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Typing indicator animation */}
      <style jsx>{`
        .typing-indicator {
          display: flex;
          gap: 4px;
        }
        .typing-indicator span {
          width: 8px;
          height: 8px;
          background: #3b82f6;
          border-radius: 50%;
          animation: bounce 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
          animation-delay: 0.4s;
        }
        @keyframes bounce {
          0%, 60%, 100% {
            transform: translateY(0);
          }
          30% {
            transform: translateY(-8px);
          }
        }
      `}</style>
    </div>
  )
}

