'use client'
/* eslint-disable */

import { useEffect, useRef, useState } from 'react'
import { Layout } from '../components/Layout'
import { Section } from '../components/Section'

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

const defaultGreeting: Message = {
  role: 'assistant',
  content: 'Hi! I can help you shortlist the right properties. Tell me your city, budget, and bedroom count to get started.',
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([defaultGreeting])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState<AgentContext | null>(null)
  const [sessionId, setSessionId] = useState<string>('')
  const [status, setStatus] = useState<string>('Ready')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initializeSession()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const initializeSession = async () => {
    try {
      const storedSessionId = localStorage.getItem('quali_session_id')
      const storedEmail = localStorage.getItem('quali_email')
      const storedPhone = localStorage.getItem('quali_phone')

      const response = await fetch(`${API_BASE}/agent/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: storedSessionId,
          email: storedEmail,
          phone: storedPhone,
        }),
      })
      if (!response.ok) {
        throw new Error(`Session request failed with ${response.status}`)
      }
      const data = await response.json()

      setSessionId(data.session_id)
      setContext(data.context)
      localStorage.setItem('quali_session_id', data.session_id)
      setStatus('Connected')

      if (data.resumed && data.context?.conversation_history) {
        const history: Message[] = []
        for (const msg of data.context.conversation_history) {
          if ((msg.role === 'user' || msg.role === 'assistant') && msg.content) {
            history.push({ role: msg.role, content: msg.content })
          }
        }
        if (history.length) {
          setMessages(history)
        }
      }

      return data
    } catch (error) {
      console.error('Failed to initialize session:', error)
      setStatus('Offline')
      return null
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    let activeSessionId = sessionId
    let activeContext = context

    if (!activeSessionId) {
      const session = await initializeSession()
      if (session?.session_id) {
        activeSessionId = session.session_id
        activeContext = session.context
      }
    }

    const userMessage = input.trim()
    setInput('')
    setLoading(true)
    setStatus('Thinking...')

    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])

    try {
      const response = await fetch(`${API_BASE}/agent/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: activeSessionId,
          context: activeContext,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('API error:', response.status, errorText)
        throw new Error(`API error: ${response.status}`)
      }

      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let assistantMessage = ''
      let currentToolCalls: Array<{ tool: string; result: any }> = []

      const handleEvent = (event: any) => {
        if (event.type === 'status') {
          setStatus(event.content || 'Working...')
          return
        }
        if (event.type === 'tool_start') {
          setStatus(`Running ${event.tool}...`)
          return
        }
        if (event.type === 'text') {
          assistantMessage += event.content
          setMessages((prev) => {
            const next = [...prev]
            const lastMessage = next[next.length - 1]
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.content = assistantMessage
              if (currentToolCalls.length) {
                lastMessage.tool_calls = [...currentToolCalls]
              }
            } else {
              next.push({
                role: 'assistant',
                content: assistantMessage,
                tool_calls: currentToolCalls.length ? [...currentToolCalls] : undefined,
              })
            }
            return next
          })
          return
        }
        if (event.type === 'tool_result') {
          currentToolCalls.push({ tool: event.tool, result: event.result })
          setMessages((prev) => {
            const next = [...prev]
            const lastMessage = next[next.length - 1]
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.tool_calls = [...currentToolCalls]
            } else {
              next.push({
                role: 'assistant',
                content: '',
                tool_calls: [...currentToolCalls],
              })
            }
            return next
          })
          return
        }
        if (event.type === 'context_update') {
          setContext(event.context)
          if (event.context?.session_id) {
            setSessionId(event.context.session_id)
            localStorage.setItem('quali_session_id', event.context.session_id)
          }
          return
        }
        if (event.type === 'complete') {
          setStatus('Complete')
          return
        }
        if (event.type === 'error') {
          setStatus('Error')
          const errorMessage = event.message || 'The assistant hit an error. Please try again.'
          setMessages((prev) => [...prev, { role: 'assistant', content: errorMessage }])
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n').filter(Boolean)
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6)
            if (data === '[DONE]') continue
            try {
              const event = JSON.parse(data)
              handleEvent(event)
            } catch (err) {
              console.error('Failed to parse SSE event:', err)
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      setStatus('Error')
      setMessages((prev) => [...prev, { role: 'assistant', content: 'I could not reach the assistant. Please check the API and try again.' }])
    } finally {
      setLoading(false)
      setStatus('Ready')
    }
  }

  return (
    <Layout title="AI Qualification Chat">
      <Section title="Assistant Status" actions={<span className="pill">{status}</span>}>
        <div style={{ color: 'var(--muted)' }}>
          Ask the assistant about lead preferences, budgets, or inventory. This chat streams tool calls and saves profiles.
        </div>
      </Section>

      <Section title="Conversation">
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className="card"
              style={{
                background: msg.role === 'user' ? 'rgba(251, 191, 36, 0.12)' : 'var(--panel-muted)',
                borderColor: msg.role === 'user' ? 'rgba(251, 191, 36, 0.4)' : 'var(--border)',
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: '0.25rem' }}>
                {msg.role === 'user' ? 'You' : 'AI'}
              </div>
              <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              {msg.tool_calls && msg.tool_calls.length > 0 && (
                <div className="pill-row" style={{ marginTop: '0.5rem' }}>
                  {msg.tool_calls.map((tc, i) => (
                    <span key={i} className="pill">{tc.tool}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </Section>

      <Section title="Send Message">
        <div className="input-row">
          <input
            className="input"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
          />
          <button className="btn" onClick={sendMessage} disabled={loading}>
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </Section>
    </Layout>
  )
}
