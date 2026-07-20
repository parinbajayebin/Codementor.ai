import React from 'react';
import { 
  Terminal, 
  MessageSquare, 
  BookOpen, 
  Activity, 
  Code2,
  GitBranch
} from 'lucide-react';

export default function Navbar({ 
  tab, 
  setTab, 
  online, 
  activeRepo, 
  repos, 
  setActiveRepo 
}) {
  return (
    <header className="cyber-card p-6 w-full space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 cyber-badge-green flex items-center justify-center font-black text-2xl shadow-[4px_4px_0px_#000]">
            <Code2 size={32} strokeWidth={3} className="text-black" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-black tracking-tight text-black">
                CODEMENTOR<span className="text-[var(--neon-pink)]">.AI</span>
              </h1>
              <span className="cyber-badge cyber-badge-yellow text-xs font-mono">
                RAG ENGINE
              </span>
            </div>
            <p className="text-xs font-mono text-gray-700 font-bold tracking-wider mt-1">
              SEMANTIC REPOSITORY SEARCH & DEEP CODE ARCHITECTURE ASSISTANT
            </p>
          </div>
        </div>

        {/* Backend Status & Active Repository Selector */}
        <div className="flex items-center flex-wrap gap-4">
          
          {/* Backend Status Badge */}
          <div className={`cyber-badge ${online ? 'cyber-badge-green' : 'cyber-badge-pink'} px-4 py-2.5 text-xs font-mono font-bold flex items-center gap-2`}>
            <Activity size={16} className={online ? 'animate-pulse' : ''} />
            <span>BACKEND: {online ? 'ONLINE 🟢' : 'OFFLINE 🔴'}</span>
          </div>

          {/* Active Repo Selector */}
          {repos && repos.length > 0 && (
            <div className="flex items-center gap-3 bg-white border-2 border-black px-4 py-2.5 shadow-[3px_3px_0px_#000]">
              <GitBranch size={18} className="text-[var(--neon-purple)]" />
              <select
                value={activeRepo ? activeRepo.repo_id : ''}
                onChange={(e) => {
                  const selected = repos.find(r => r.repo_id === e.target.value);
                  if (selected) setActiveRepo(selected);
                }}
                className="bg-transparent font-mono text-xs font-bold text-black outline-none cursor-pointer"
              >
                {repos.map(r => (
                  <option key={r.repo_id} value={r.repo_id} className="bg-white text-black">
                    {r.repo_id} ({r.total_chunks || 0} chunks)
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Main Tab Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 border-t-2 border-black">
        <button
          onClick={() => setTab('ingest')}
          className={`cyber-btn py-4 justify-center ${
            tab === 'ingest' ? 'cyber-btn-green' : 'hover:bg-gray-100'
          }`}
        >
          <Terminal size={20} />
          1. INGEST REPOSITORY
        </button>

        <button
          onClick={() => setTab('chat')}
          className={`cyber-btn py-4 justify-center ${
            tab === 'chat' ? 'cyber-btn-cyan' : 'hover:bg-gray-100'
          }`}
        >
          <MessageSquare size={20} />
          2. RAG CHAT & MENTOR
        </button>

        <button
          onClick={() => setTab('onboarding')}
          className={`cyber-btn py-4 justify-center ${
            tab === 'onboarding' ? 'cyber-btn-yellow' : 'hover:bg-gray-100'
          }`}
        >
          <BookOpen size={20} />
          3. ONBOARDING GUIDE
        </button>
      </div>
    </header>
  );
}
