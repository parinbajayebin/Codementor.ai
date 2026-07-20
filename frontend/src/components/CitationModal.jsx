import React, { useState, useMemo } from 'react';
import { X, Copy, Check, FileCode, Target, Hash, Percent, ShieldCheck } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

/**
 * Map backend language strings to react-syntax-highlighter language identifiers.
 * Falls back to "text" if unknown.
 */
const LANG_MAP = {
  python: 'python',
  javascript: 'javascript',
  jsx: 'jsx',
  typescript: 'typescript',
  tsx: 'tsx',
  java: 'java',
  c: 'c',
  cpp: 'cpp',
  csharp: 'csharp',
  go: 'go',
  rust: 'rust',
  ruby: 'ruby',
  php: 'php',
  swift: 'swift',
  kotlin: 'kotlin',
  scala: 'scala',
  r: 'r',
  lua: 'lua',
  bash: 'bash',
  powershell: 'powershell',
  sql: 'sql',
  html: 'html',
  css: 'css',
  scss: 'scss',
  less: 'less',
  xml: 'xml',
  json: 'json',
  yaml: 'yaml',
  toml: 'toml',
  ini: 'ini',
  markdown: 'markdown',
  dockerfile: 'dockerfile',
  makefile: 'makefile',
  text: 'text',
};

/** Custom one-dark theme overrides to match our Neo-Brutalist cards */
const customStyle = {
  ...oneDark,
  'pre[class*="language-"]': {
    ...oneDark['pre[class*="language-"]'],
    margin: 0,
    padding: '1.25rem',
    fontSize: '0.8rem',
    lineHeight: '1.7',
    background: '#1a1b26',
    border: 'none',
    borderRadius: 0,
  },
  'code[class*="language-"]': {
    ...oneDark['code[class*="language-"]'],
    fontSize: '0.8rem',
    fontFamily: "'JetBrains Mono', monospace",
  },
};

export default function CitationModal({ citation, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(citation.content_preview || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lang = LANG_MAP[citation.language] || LANG_MAP['text'] || 'text';
  const langLabel = (citation.language || 'text').toUpperCase();

  const confColor = {
    high: 'cyber-badge-green',
    medium: 'cyber-badge-yellow',
    low: 'cyber-badge-pink',
  }[citation.confidence?.toLowerCase()] || 'cyber-badge-yellow';

  const confIcon = {
    high: '🟢',
    medium: '🟡',
    low: '🔴',
  }[citation.confidence?.toLowerCase()] || '🟡';

  // Calculate total lines in chunk
  const totalLines = (citation.content_preview || '').split('\n').length;

  // Relevance bar width (capped 0-100%)
  const relevancePercent = citation.relevance_score
    ? Math.min(100, Math.round(citation.relevance_score * 100))
    : 0;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="cyber-card bg-white w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden border-2 border-black"
        style={{ boxShadow: '8px 8px 0px #000000', marginBottom: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-yellow-200 border-b-2 border-black shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-black font-mono flex items-center gap-2 text-black">
              <FileCode size={18} /> SOURCE CITATION [{citation.source_number}]
            </span>
            <span className="cyber-badge cyber-badge-purple text-[10px]">
              {langLabel}
            </span>
          </div>
          <button 
            onClick={onClose} 
            className="cyber-btn cyber-btn-pink py-1 px-2 text-xs"
            style={{ marginBottom: 0 }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="p-5 space-y-5 font-mono text-xs overflow-y-auto flex-1">
          
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 border-2 border-black bg-gray-50 shadow-[3px_3px_0px_#000]">
            <div>
              <span className="block text-[10px] font-black text-gray-600 uppercase mb-1.5 tracking-wider">FILE PATH</span>
              <span className="font-bold text-black break-all text-xs">{citation.file_path}</span>
            </div>
            <div>
              <span className="block text-[10px] font-black text-gray-600 uppercase mb-1.5 tracking-wider flex items-center gap-1">
                <Hash size={10} /> LINE RANGE
              </span>
              <span className="font-black text-purple-700 text-sm">
                L{citation.start_line} — L{citation.end_line}
              </span>
              <span className="block text-[10px] text-gray-500 mt-0.5">{totalLines} lines in chunk</span>
            </div>
            <div>
              <span className="block text-[10px] font-black text-gray-600 uppercase mb-1.5 tracking-wider flex items-center gap-1">
                <Percent size={10} /> RELEVANCE
              </span>
              <span className="font-black text-sm text-black">
                {relevancePercent}%
              </span>
              {/* Visual relevance bar */}
              <div className="w-full h-2.5 bg-gray-200 border border-black mt-1.5">
                <div 
                  className="h-full transition-all"
                  style={{ 
                    width: `${relevancePercent}%`,
                    backgroundColor: relevancePercent >= 85 ? '#00e659' : relevancePercent >= 70 ? '#ffdd00' : '#ff2a75'
                  }}
                />
              </div>
            </div>
            <div>
              <span className="block text-[10px] font-black text-gray-600 uppercase mb-1.5 tracking-wider flex items-center gap-1">
                <ShieldCheck size={10} /> CONFIDENCE
              </span>
              <span className={`cyber-badge ${confColor} text-xs`} style={{ marginBottom: 0 }}>
                {confIcon} {citation.confidence?.toUpperCase() || 'MEDIUM'}
              </span>
            </div>
          </div>

          {/* Syntax Highlighted Code Block */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-black text-black flex items-center gap-2">
                <Target size={14} className="text-purple-700" /> 
                RETRIEVED SOURCE CODE CHUNK
                <span className="cyber-badge cyber-badge-cyan text-[9px]" style={{ marginBottom: 0 }}>
                  {langLabel} • L{citation.start_line}–L{citation.end_line}
                </span>
              </span>
              <button 
                onClick={handleCopy} 
                className="cyber-btn text-xs py-1.5 px-4 bg-white"
                style={{ marginBottom: 0 }}
              >
                {copied ? <Check size={14} className="text-green-700" /> : <Copy size={14} />}
                {copied ? 'COPIED!' : 'COPY CODE'}
              </button>
            </div>

            <div className="border-2 border-black shadow-[4px_4px_0px_#000] overflow-hidden">
              {/* File path tab bar */}
              <div className="bg-gray-900 text-gray-400 px-4 py-2 text-[11px] font-mono font-bold flex items-center justify-between border-b border-gray-700">
                <span>📄 {citation.file_path}</span>
                <span className="text-gray-500">Lines {citation.start_line}–{citation.end_line}</span>
              </div>

              {/* Syntax highlighted code */}
              <div className="max-h-[350px] overflow-auto">
                <SyntaxHighlighter
                  language={lang}
                  style={customStyle}
                  showLineNumbers={true}
                  startingLineNumber={citation.start_line || 1}
                  wrapLongLines={true}
                  lineNumberStyle={{
                    minWidth: '3em',
                    paddingRight: '1em',
                    color: '#555',
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '0.7rem',
                    userSelect: 'none',
                  }}
                >
                  {citation.content_preview || '// No source code available'}
                </SyntaxHighlighter>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-gray-100 border-t-2 border-black flex items-center justify-between shrink-0">
          <span className="font-mono text-[10px] text-gray-500 font-bold">
            VECTOR CHUNK SOURCE • COSINE SIMILARITY RETRIEVAL
          </span>
          <button 
            onClick={onClose} 
            className="cyber-btn cyber-btn-yellow py-2 px-6 text-xs"
            style={{ marginBottom: 0 }}
          >
            CLOSE PREVIEW
          </button>
        </div>
      </div>
    </div>
  );
}
