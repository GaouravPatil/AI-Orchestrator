import { useState, useEffect, useRef } from 'react';
import '../styles/AIChat.css';
import { sendChat } from '../services/api';

const STARTER_PROMPTS = [
  'List all nodes in the cluster',
  'How many pods are running?',
  'Show all deployments',
  'List namespaces',
];

export default function AIChat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello. I'm your AI DevOps assistant. I have direct access to your Kubernetes cluster — ask me anything about nodes, pods, deployments, logs, or let me take actions on your behalf.",
      steps: [],
    },
  ]);
  const [input, setInput]           = useState('');
  const [loading, setLoading]       = useState(false);
  const [convId, setConvId]         = useState(null);
  const [namespace, setNamespace]   = useState('default');
  const bottomRef                   = useRef(null);
  const inputRef                    = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const res = await sendChat(msg, convId, namespace);
      setConvId(res.conversation_id);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.answer,
        steps: res.steps ?? [],
        model: res.model,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠ Error: ${err.response?.data?.detail ?? err.message}`,
        error: true,
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="aichat">
      {/* Header */}
      <div className="aichat-header">
        <div className="aichat-header-left">
          <div className="ai-orb">
            <span className="ai-orb-inner" />
          </div>
          <div>
            <h3 className="font-orbitron">AI ASSISTANT</h3>
            <p>llama3 via Ollama · k8s-aware agent</p>
          </div>
        </div>
        <div className="aichat-header-right">
          <label className="ns-label font-mono">NS</label>
          <select
            className="ns-select"
            value={namespace}
            onChange={e => setNamespace(e.target.value)}
          >
            {['default','kube-system','kube-public'].map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages */}
      <div className="aichat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role} ${m.error ? 'error' : ''} animate-fade-up`}>
            <div className="chat-avatar">
              {m.role === 'user'
                ? <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12a5 5 0 100-10 5 5 0 000 10zm0 2c-5.33 0-8 2.67-8 4v2h16v-2c0-1.33-2.67-4-8-4z"/></svg>
                : <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/></svg>
              }
            </div>
            <div className="chat-bubble">
              <pre className="chat-text">{m.content}</pre>
              {/* Tool steps */}
              {m.steps?.filter(s => s.tool_calls?.length > 0).map((s, si) => (
                <div key={si} className="chat-step">
                  <span className="step-label font-mono">
                    ⚡ {s.thought || 'tool call'} →
                  </span>
                  {s.tool_calls.map((tc, ti) => (
                    <span key={ti} className="badge badge-cyan">{tc.name}</span>
                  ))}
                </div>
              ))}
              {m.model && (
                <span className="chat-meta font-mono">{m.model}</span>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-msg assistant">
            <div className="chat-avatar">
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09 3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/></svg>
            </div>
            <div className="chat-bubble">
              <div className="chat-typing">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starters */}
      {messages.length === 1 && (
        <div className="chat-starters">
          {STARTER_PROMPTS.map((p, i) => (
            <button key={i} className="starter-btn" onClick={() => send(p)}>
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="aichat-input-row">
        <textarea
          ref={inputRef}
          id="ai-chat-input"
          className="aichat-input"
          placeholder="Ask anything about your cluster…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          rows={1}
          disabled={loading}
        />
        <button
          id="ai-chat-send"
          className="btn btn-primary aichat-send"
          onClick={() => send()}
          disabled={loading || !input.trim()}
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        </button>
      </div>
    </div>
  );
}
