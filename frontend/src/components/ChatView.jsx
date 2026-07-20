import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Trash2, 
  MessageSquare, 
  Sparkles, 
  FileCode2, 
  HelpCircle,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { api } from '../services/api';
import CitationModal from './CitationModal';

const SUGGESTED_PROMPTS = [
  "How does routing work in this codebase?",
  "Where is the main application entry point?",
  "How is error handling and logging structured?",
  "What design patterns or architecture are used?",
];

/** Inline code block style overrides */
const inlineCodeStyle = {
  ...oneDark,
  'pre[class*="language-"]': {
    ...oneDark['pre[class*="language-"]'],
    margin: 0,
    padding: '0.75rem 1rem',
    fontSize: '0.75rem',
    lineHeight: '1.6',
    background: '#1a1b26',
    border: 'none',
    borderRadius: 0,
  },
  'code[class*="language-"]': {
    ...oneDark['code[class*="language-"]'],
    fontSize: '0.75rem',
    fontFamily: "'JetBrains Mono', monospace",
  },
};

export default function ChatView({ activeRepo, showToast }) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (activeRepo && activeRepo.repo_id) {
      loadHistory(activeRepo.repo_id);
    }
  }, [activeRepo]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadHistory = async (repoId) => {
    try {
      const data = await api.getChatHistory(repoId);
      if (data && data.messages) {
        setMessages(data.messages);
      }
    } catch {
      setMessages([]);
    }
  };

  const handleAsk = async (queryText = question) => {
    if (!queryText.trim()) return;
    if (!activeRepo) {
      showToast('Please select or ingest a repository first!', 'error');
      return;
    }

    const currentQuery = queryText.trim();
    setQuestion('');

    const userMsg = {
      role: 'user',
      content: currentQuery,
      timestamp: Date.now() / 1000,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.askQuestion(activeRepo.repo_id, currentQuery);
      
      const assistantMsg = {
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
        timestamp: Date.now() / 1000,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      showToast(`RAG Query Error: ${err.message}`, 'error');
      const errorMsg = {
        role: 'assistant',
        content: `⚠️ **Error generating answer:** ${err.message}. Please check if backend services are active.`,
        citations: [],
        timestamp: Date.now() / 1000,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!activeRepo) return;
    if (!window.confirm(`Clear chat history for repository '${activeRepo.repo_id}'?`)) return;

    try {
      await api.clearChatHistory(activeRepo.repo_id);
      setMessages([]);
      showToast('Chat history cleared', 'info');
    } catch (err) {
      showToast(`Failed to clear history: ${err.message}`, 'error');
    }
  };

  /**
   * Render AI answer with:
   * 1. Clickable [Source N] citation badges
   * 2. Syntax-highlighted ```lang code blocks
   * 3. Inline `code` formatting
   * 4. **bold** text
   */
  const renderFormattedAnswer = (content, citations = []) => {
    if (!content) return null;

    // Split on fenced code blocks first: ```lang\ncode\n```
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const segments = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Text before the code block
      if (match.index > lastIndex) {
        segments.push({ type: 'text', content: content.slice(lastIndex, match.index) });
      }
      // Code block
      segments.push({ type: 'code', language: match[1] || 'text', content: match[2] });
      lastIndex = match.index + match[0].length;
    }
    // Remaining text after the last code block
    if (lastIndex < content.length) {
      segments.push({ type: 'text', content: content.slice(lastIndex) });
    }

    return (
      <div className="font-sans text-sm space-y-3 leading-relaxed text-black">
        {segments.map((seg, segIdx) => {
          if (seg.type === 'code') {
            return (
              <div key={segIdx} className="border-2 border-black shadow-[3px_3px_0px_#000] overflow-hidden" style={{ marginBottom: 0 }}>
                <div className="bg-gray-900 text-gray-400 px-3 py-1.5 text-[10px] font-mono font-bold flex items-center justify-between border-b border-gray-700">
                  <span>📄 {seg.language.toUpperCase()}</span>
                </div>
                <SyntaxHighlighter
                  language={seg.language}
                  style={inlineCodeStyle}
                  wrapLongLines={true}
                >
                  {seg.content.trim()}
                </SyntaxHighlighter>
              </div>
            );
          }

          // Text segment: handle [Source N] citations, **bold**, and `inline code`
          const parts = seg.content.split(/(\[Source\s+\d+\]|`[^`]+`|\*\*[^*]+\*\*)/gi);

          return (
            <span key={segIdx}>
              {parts.map((part, i) => {
                // Citation badge
                const sourceMatch = part.match(/\[Source\s+(\d+)\]/i);
                if (sourceMatch) {
                  const sourceNum = parseInt(sourceMatch[1], 10);
                  const foundCitation = citations.find((c) => c.source_number === sourceNum);
                  return (
                    <button
                      key={`${segIdx}-${i}`}
                      onClick={() => {
                        if (foundCitation) {
                          setSelectedCitation(foundCitation);
                        } else {
                          showToast(`Source [${sourceNum}] chunk reference`, 'info');
                        }
                      }}
                      className="cyber-badge cyber-badge-yellow cursor-pointer mx-1 inline-flex items-center gap-1 hover:translate-y-[-2px] transition-transform"
                      style={{ marginBottom: 0 }}
                      title={foundCitation ? `Click to view ${foundCitation.file_path} L${foundCitation.start_line}-${foundCitation.end_line}` : 'Source citation'}
                    >
                      <FileCode2 size={12} />
                      [{sourceNum}] {foundCitation ? foundCitation.file_path.split('/').pop() : ''}
                    </button>
                  );
                }

                // Inline code: `something`
                const inlineMatch = part.match(/^`([^`]+)`$/);
                if (inlineMatch) {
                  return (
                    <code
                      key={`${segIdx}-${i}`}
                      className="bg-gray-900 text-green-400 px-1.5 py-0.5 mx-0.5 text-xs font-mono border border-black"
                    >
                      {inlineMatch[1]}
                    </code>
                  );
                }

                // Bold: **something**
                const boldMatch = part.match(/^\*\*([^*]+)\*\*$/);
                if (boldMatch) {
                  return <strong key={`${segIdx}-${i}`}>{boldMatch[1]}</strong>;
                }

                return <span key={`${segIdx}-${i}`}>{part}</span>;
              })}
            </span>
          );
        })}
      </div>
    );
  };

  if (!activeRepo) {
    return (
      <div className="cyber-card p-12 text-center space-y-4">
        <AlertCircle size={48} className="mx-auto text-[var(--neon-pink)]" />
        <h3 className="text-2xl font-black text-black">NO ACTIVE REPOSITORY SELECTED</h3>
        <p className="font-mono text-sm text-gray-700 max-w-md mx-auto font-bold">
          Please ingest or select a repository from the <strong>"1. INGEST REPOSITORY"</strong> tab 
          to start asking RAG questions grounded in code.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full">
      
      {/* Selected Repo Header Bar */}
      <div className="cyber-card cyber-card-cyan p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="font-mono text-xs font-bold uppercase text-black">ACTIVE REPOSITORY CONTEXT:</span>
          <h2 className="text-2xl font-black tracking-tight text-black flex items-center gap-2">
            <Sparkles size={24} className="text-black" />
            {activeRepo.repo_id}
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <span className="cyber-badge cyber-badge-yellow text-xs">
            {activeRepo.total_chunks || 'Indexed'} CHUNKS
          </span>
          <button
            onClick={handleClearHistory}
            className="cyber-btn cyber-btn-pink text-xs py-2 px-3"
            title="Clear Chat History"
          >
            <Trash2 size={14} /> CLEAR HISTORY
          </button>
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="cyber-card p-4">
        <span className="font-mono text-xs font-bold text-gray-700 uppercase block mb-3">
          💡 SUGGESTED QUESTIONS:
        </span>
        <div className="flex flex-wrap gap-3">
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleAsk(prompt)}
              disabled={loading}
              className="cyber-btn text-xs py-2 px-3 bg-white hover:bg-gray-100"
            >
              <HelpCircle size={14} className="text-[var(--neon-purple)]" />
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="cyber-card p-6 min-h-[500px] max-h-[650px] overflow-y-auto space-y-6 font-mono bg-white">
        {messages.length === 0 ? (
          <div className="p-12 text-center border-2 border-dashed border-black bg-yellow-50 text-gray-800 space-y-3">
            <MessageSquare size={40} className="mx-auto text-[var(--neon-purple)]" />
            <p className="font-bold text-base text-black">NO CONVERSATION YET</p>
            <p className="text-xs font-bold">Ask any architectural or code structure question about <strong>{activeRepo.repo_id}</strong>!</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`max-w-[90%] md:max-w-[85%] p-5 border-2 border-black shadow-[4px_4px_0px_#000] ${
                  msg.role === 'user'
                    ? 'bg-yellow-300 text-black font-bold'
                    : 'bg-white text-black'
                }`}
              >
                <div className="flex items-center justify-between gap-4 mb-3 pb-2 border-b border-black/20">
                  <span className="font-black text-xs uppercase flex items-center gap-2 text-black">
                    {msg.role === 'user' ? '👤 YOU' : '🤖 CODEMENTOR AI'}
                  </span>
                  <span className="text-[10px] opacity-75 font-mono text-black font-bold">
                    {msg.timestamp ? new Date(msg.timestamp * 1000).toLocaleTimeString() : ''}
                  </span>
                </div>

                {msg.role === 'user' ? (
                  <p className="font-sans font-bold text-sm leading-relaxed text-black">
                    {msg.content}
                  </p>
                ) : (
                  renderFormattedAnswer(msg.content, msg.citations)
                )}

                {/* Citations Preview Footer */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-dashed border-black/20 flex flex-wrap gap-2 items-center">
                    <span className="text-[11px] font-bold uppercase text-black">SOURCE CITATIONS:</span>
                    {msg.citations.map((c, cIdx) => (
                      <button
                        key={cIdx}
                        onClick={() => setSelectedCitation(c)}
                        className="cyber-badge cyber-badge-yellow text-xs cursor-pointer"
                      >
                        [{c.source_number}] {c.file_path.split('/').pop()} (L{c.start_line}-{c.end_line})
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-center gap-3 p-4 cyber-card cyber-card-yellow animate-pulse max-w-md font-mono text-xs font-bold text-black">
            <Loader2 size={18} className="animate-spin text-black" />
            <span>SEARCHING QDRANT VECTORS & GENERATING ANSWER VIA QWEN LLM...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="flex gap-4">
        <input
          type="text"
          placeholder={`Ask a question about ${activeRepo.repo_id}... (e.g. How does error handling work?)`}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
          disabled={loading}
          className="cyber-input flex-1 text-base py-3.5"
        />
        <button
          onClick={() => handleAsk()}
          disabled={loading || !question.trim()}
          className="cyber-btn cyber-btn-green text-base py-3.5 px-8"
        >
          {loading ? <Loader2 size={18} className="animate-spin text-black" /> : <Send size={18} className="text-black" />}
          ASK MENTOR
        </button>
      </div>

      {/* Citation Details Modal */}
      {selectedCitation && (
        <CitationModal
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </div>
  );
}
