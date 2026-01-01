import { useEffect, useRef, useState } from 'react';
import { Send, Sparkles, ExternalLink, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getUnitImage } from '@/lib/images';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface ToolCall {
  tool: string;
  result: any;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  tool_calls?: ToolCall[];
}

interface AgentContext {
  conversation_history: any[];
  collected_data: Record<string, any>;
  tool_call_count: number;
  lead_id?: number;
  session_id?: string;
}

export default function QualificationChat({
  variant = 'page',
  onOpenFull,
  onClose,
}: {
  variant?: 'page' | 'widget' | 'admin';
  onOpenFull?: () => void;
  onClose?: () => void;
}) {
  const greeting = "Welcome to Abriqot. What's your first name?";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [status, setStatus] = useState('Ready');
  const [context, setContext] = useState<AgentContext | null>(null);
  const [sessionId, setSessionId] = useState('');
  const [needsContextSync, setNeedsContextSync] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const isCompact = variant === 'widget';
  const scrollHeightClass = isCompact ? 'max-h-64' : 'h-[60vh] md:h-[70vh]';
  const wrapperClass =
    variant === 'page'
      ? 'space-y-4'
      : `bg-card border border-border rounded-2xl ${isCompact ? 'p-4' : 'p-6'} space-y-4`;

  useEffect(() => {
    initializeSession();
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('quali_messages:last', JSON.stringify(messages));
      if (sessionId) {
        localStorage.setItem(`quali_messages:${sessionId}`, JSON.stringify(messages));
      }
    } catch (error) {
      console.error('Failed to persist messages:', error);
    }
  }, [messages, sessionId]);

  useEffect(() => {
    if (!context) return;
    try {
      localStorage.setItem('quali_context:last', JSON.stringify(context));
      if (sessionId) {
        localStorage.setItem(`quali_context:${sessionId}`, JSON.stringify(context));
      }
    } catch (error) {
      console.error('Failed to persist context:', error);
    }
  }, [context, sessionId]);

  useEffect(() => {
    if (!autoScroll) return;
    const container = scrollRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages, autoScroll]);

  const initializeSession = async () => {
    try {
      const storedSessionId = localStorage.getItem('quali_session_id');
      const storedEmail = localStorage.getItem('quali_email');
      const storedPhone = localStorage.getItem('quali_phone');
      const cachedMessages = storedSessionId
        ? localStorage.getItem(`quali_messages:${storedSessionId}`)
        : localStorage.getItem('quali_messages:last');
      const cachedContext = storedSessionId
        ? localStorage.getItem(`quali_context:${storedSessionId}`)
        : localStorage.getItem('quali_context:last');

      if (storedSessionId) {
        setSessionId(storedSessionId);
      }

      let cachedContextValue: AgentContext | null = null;
      if (cachedContext) {
        try {
          const parsedContext = JSON.parse(cachedContext);
          if (parsedContext?.conversation_history?.length) {
            cachedContextValue = parsedContext;
            setContext(parsedContext);
          }
        } catch (error) {
          console.error('Failed to read cached context:', error);
        }
      }

      let cachedMessagesValue: Message[] | null = null;
      if (cachedMessages) {
        try {
          const parsed = JSON.parse(cachedMessages);
          if (Array.isArray(parsed) && parsed.length) {
            cachedMessagesValue = parsed;
            setMessages(parsed);
          }
        } catch (error) {
          console.error('Failed to read cached messages:', error);
        }
      }

      const response = await fetch(`${API_BASE}/agent/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: storedSessionId,
          email: storedEmail,
          phone: storedPhone,
        }),
      });

      if (!response.ok) {
        throw new Error(`Session request failed with ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      localStorage.setItem('quali_session_id', data.session_id);
      const resumeSucceeded = Boolean(data.resumed);
      let syncContext: AgentContext | null = null;
      if (!resumeSucceeded && cachedContextValue?.conversation_history?.length) {
        setNeedsContextSync(true);
        syncContext = { ...cachedContextValue, session_id: data.session_id };
        setContext(syncContext);
      } else {
        setNeedsContextSync(false);
        setContext(data.context);
      }
      setStatus('Connected');

      const history: Message[] = [];
      if (data.context?.conversation_history) {
        for (const msg of data.context.conversation_history) {
          if ((msg.role === 'user' || msg.role === 'assistant') && msg.content) {
            history.push({ role: msg.role, content: msg.content });
          }
        }
      }
      if (history.length && history[0].role === 'assistant') {
        const firstContent = history[0].content.toLowerCase();
        if (firstContent.includes('shortlist the right properties')) {
          history[0].content = greeting;
        }
      }
      const cachedLength = cachedMessagesValue ? cachedMessagesValue.length : 0;
      if (!history.length) {
        history.push({ role: 'assistant', content: greeting });
      }
      if (history.length && data.context?.collected_data?.matches?.length) {
        const last = history[history.length - 1];
        if (last.role === 'assistant') {
          last.tool_calls = [
            {
              tool: 'inventory_search',
              result: data.context.collected_data.matches,
            },
          ];
        }
      }
      if (history.length && history.length >= cachedLength) {
        setMessages(history);
      }
      return {
        session_id: data.session_id as string,
        context: data.context as AgentContext,
        syncContext,
      };
    } catch (error) {
      console.error('Failed to initialize session:', error);
      setStatus('Offline');
      const storedSessionId = localStorage.getItem('quali_session_id');
      const cachedMessages = storedSessionId
        ? localStorage.getItem(`quali_messages:${storedSessionId}`)
        : localStorage.getItem('quali_messages:last');
      const cachedContext = storedSessionId
        ? localStorage.getItem(`quali_context:${storedSessionId}`)
        : localStorage.getItem('quali_context:last');
      if (cachedContext) {
        try {
          const parsedContext = JSON.parse(cachedContext);
          if (parsedContext?.conversation_history?.length) {
            const cachedHistory: Message[] = [];
            for (const msg of parsedContext.conversation_history) {
              if ((msg.role === 'user' || msg.role === 'assistant') && msg.content) {
                cachedHistory.push({ role: msg.role, content: msg.content });
              }
            }
            if (cachedHistory.length) {
              setContext(parsedContext);
              setMessages(cachedHistory);
              return null;
            }
          }
        } catch (cachedError) {
          console.error('Failed to read cached context:', cachedError);
        }
      }
      if (cachedMessages) {
        try {
          const parsed = JSON.parse(cachedMessages);
          if (Array.isArray(parsed) && parsed.length) {
            setMessages(parsed);
            return null;
          }
        } catch (cachedError) {
          console.error('Failed to read cached messages:', cachedError);
        }
      }
      setMessages((prev) => (prev.length ? prev : [{ role: 'assistant', content: greeting }]));
      return null;
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    let activeSessionId = sessionId;
    let syncContext = needsContextSync ? context : null;

    if (!activeSessionId) {
      const session = await initializeSession();
      if (session) {
        activeSessionId = session.session_id;
        if (session.syncContext) {
          syncContext = session.syncContext;
        }
      } else {
        setStatus('Offline');
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'I could not connect the assistant. Please try again.' },
        ]);
        return;
      }
    }

    const userMessage = input.trim();
    setInput('');
    setLoading(true);
    setIsTyping(true);
    setStatus('Thinking...');

    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    try {
      const response = await fetch(`${API_BASE}/agent/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: activeSessionId,
          ...(syncContext ? { context: { ...syncContext, session_id: activeSessionId } } : {}),
        }),
      });

      if (!response.ok || !response.body) {
        const errorText = await response.text();
        throw new Error(errorText || `API error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let assistantMessage = '';
      let currentToolCalls: ToolCall[] = [];

      const handleEvent = (event: any) => {
        if (event.type === 'status') {
          setStatus(event.content || 'Working...');
          return;
        }
        if (event.type === 'tool_start') {
          setStatus(`Running ${event.tool}...`);
          return;
        }
        if (event.type === 'text') {
          assistantMessage += event.content;
          setIsTyping(false);
          setMessages((prev) => {
            const next = [...prev];
            const lastMessage = next[next.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.content = assistantMessage;
              if (currentToolCalls.length) {
                lastMessage.tool_calls = [...currentToolCalls];
              }
            } else {
              next.push({ role: 'assistant', content: assistantMessage, tool_calls: currentToolCalls });
            }
            return next;
          });
          return;
        }
        if (event.type === 'tool_result') {
          currentToolCalls = [...currentToolCalls, { tool: event.tool, result: event.result }];
          setMessages((prev) => {
            const next = [...prev];
            const lastMessage = next[next.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.tool_calls = [...currentToolCalls];
            }
            return next;
          });
          return;
        }
        if (event.type === 'context_update') {
          setContext(event.context);
          setNeedsContextSync(false);
          if (event.context?.session_id) {
            setSessionId(event.context.session_id);
            localStorage.setItem('quali_session_id', event.context.session_id);
          }
          if (event.context?.collected_data) {
            const email = event.context.collected_data.contact_email || event.context.collected_data.email || '';
            const phone = event.context.collected_data.contact_phone || event.context.collected_data.phone || '';
            if (email) {
              localStorage.setItem('quali_email', email);
            }
            if (phone) {
              localStorage.setItem('quali_phone', phone);
            }
          }
          return;
        }
        if (event.type === 'complete') {
          setStatus('Complete');
          setIsTyping(false);
          return;
        }
        if (event.type === 'error') {
          setStatus('Error');
          setIsTyping(false);
          const errorMessage = event.message || 'The assistant hit an error. Please try again.';
          setMessages((prev) => [...prev, { role: 'assistant', content: errorMessage }]);
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          const lines = part.split('\n').filter(Boolean);
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            try {
              const event = JSON.parse(data);
              handleEvent(event);
            } catch (err) {
              console.error('Failed to parse SSE event:', err);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setStatus('Error');
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'I could not reach the assistant. Please check the API and try again.' },
      ]);
    } finally {
      setLoading(false);
      setStatus('Ready');
      setIsTyping(false);
    }
  };

  const renderMatches = (toolCalls?: ToolCall[]) => {
    if (!toolCalls || toolCalls.length === 0) return null;
    const inventoryCall = toolCalls.find((call) => call.tool === 'inventory_search');
    if (!inventoryCall) return null;
    const matches = Array.isArray(inventoryCall.result)
      ? inventoryCall.result
      : inventoryCall.result?.matches || [];
    if (!matches.length) return null;

    return (
      <div className="grid gap-3 mt-3">
        {matches.map((match: any) => {
          const image = getUnitImage(match);
          const href = match.slug ? `/investments/${match.slug}` : `/investments/${match.unit_id}`;
          return (
            <Link
              key={match.unit_id || match.slug}
              to={href}
              className="flex gap-3 p-3 rounded-xl border border-border bg-background/60 hover:border-primary/40 transition-colors"
            >
              <div className="w-20 h-20 rounded-lg overflow-hidden bg-muted flex-shrink-0">
                {image ? (
                  <img src={image} alt={match.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-xs text-muted-foreground">
                    No image
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-foreground truncate">{match.title}</p>
                    <p className="text-xs text-muted-foreground">{match.developer || 'Developer'}</p>
                  </div>
                  <span className="text-sm font-semibold text-foreground">
                    {match.price_display || `${match.currency || 'AED'} ${match.price || ''}`}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                  {match.handover && <span className="px-2 py-0.5 rounded-full bg-muted">{match.handover}</span>}
                  {match.payment_plan && (
                    <span className="px-2 py-0.5 rounded-full bg-muted">{match.payment_plan}</span>
                  )}
                  {match.roi && <span className="px-2 py-0.5 rounded-full bg-muted">{match.roi} ROI</span>}
                </div>
                {match.location && <p className="text-xs text-muted-foreground mt-2">{match.location}</p>}
              </div>
            </Link>
          );
        })}
      </div>
    );
  };

  const showHeader = variant !== 'page';
  const showRoleLabel = variant !== 'page';

  return (
    <div className={wrapperClass}>
      {showHeader && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <div>
              <p className="text-sm font-semibold text-foreground">Qualification assistant</p>
              <p className="text-xs text-muted-foreground">Status: {status}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onOpenFull && (
              <button
                onClick={onOpenFull}
                className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
              >
                Full view
                <ExternalLink className="w-3 h-3" />
              </button>
            )}
            {onClose && (
              <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}

      <div
        ref={scrollRef}
        onScroll={() => {
          const container = scrollRef.current;
          if (!container) return;
          const distance = container.scrollHeight - container.scrollTop - container.clientHeight;
          setAutoScroll(distance < 80);
        }}
        className={`${scrollHeightClass} overflow-y-auto space-y-3 pr-1 flex flex-col`}
      >
        {messages.length === 0 && (
          <div className="rounded-xl border px-4 py-3 text-sm bg-muted/40 border-border text-foreground max-w-[70%] self-start">
            {showRoleLabel && <p className="text-xs text-muted-foreground mb-1">Assistant</p>}
            <p className="whitespace-pre-wrap">{greeting}</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`rounded-xl border px-4 py-3 text-sm ${
              msg.role === 'user'
                ? 'bg-primary/10 border-primary/30 text-foreground ml-auto self-end text-right'
                : 'bg-muted/40 border-border text-foreground self-start'
            }`}
            style={{ maxWidth: '70%' }}
          >
            {showRoleLabel && (
              <p className="text-xs text-muted-foreground mb-1">{msg.role === 'user' ? 'You' : 'Assistant'}</p>
            )}
            <p className="whitespace-pre-wrap">{msg.content}</p>
            {renderMatches(msg.tool_calls)}
            {variant === 'admin' && msg.tool_calls && msg.tool_calls.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {msg.tool_calls.map((toolCall, index) => (
                  <span key={index} className="text-[11px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                    {toolCall.tool}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {isTyping && (
          <div className="rounded-xl border px-4 py-3 text-sm bg-muted/40 border-border text-foreground max-w-[70%] self-start">
            {showRoleLabel && <p className="text-xs text-muted-foreground mb-1">Assistant</p>}
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:-0.2s]" />
              <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:-0.1s]" />
              <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" />
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Type your message..."
          className="flex-1 px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
          disabled={loading}
        />
        <button onClick={sendMessage} className="btn-primary" disabled={loading}>
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
