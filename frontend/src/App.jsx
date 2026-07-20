import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import IngestView from './components/IngestView';
import ChatView from './components/ChatView';
import OnboardingView from './components/OnboardingView';
import Toast from './components/Toast';
import { api } from './services/api';
import { Terminal, GitBranch } from 'lucide-react';

export default function App() {
  const [tab, setTab] = useState('ingest');
  const [online, setOnline] = useState(false);
  const [repos, setRepos] = useState([]);
  const [activeRepo, setActiveRepo] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    checkHealth();
    fetchRepos();
    const timer = setInterval(checkHealth, 15000);
    return () => clearInterval(timer);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await api.healthCheck();
      setOnline(res?.status === 'healthy');
    } catch {
      setOnline(false);
    }
  };

  const fetchRepos = async () => {
    try {
      const data = await api.listRepos();
      if (Array.isArray(data)) {
        setRepos(data);
        if (data.length > 0 && !activeRepo) {
          setActiveRepo(data[0]);
        }
      }
    } catch {
      setRepos([]);
    }
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  return (
    <div className="min-h-screen w-full flex flex-col p-6 lg:p-10 space-y-8">
      {/* Top Navbar */}
      <Navbar
        tab={tab}
        setTab={setTab}
        online={online}
        activeRepo={activeRepo}
        repos={repos}
        setActiveRepo={setActiveRepo}
      />

      {/* Main View Area */}
      <main className="flex-1 w-full space-y-8">
        {tab === 'ingest' && (
          <IngestView
            repos={repos}
            fetchRepos={fetchRepos}
            setActiveRepo={setActiveRepo}
            setTab={setTab}
            showToast={showToast}
          />
        )}
        {tab === 'chat' && (
          <ChatView
            activeRepo={activeRepo}
            showToast={showToast}
          />
        )}
        {tab === 'onboarding' && (
          <OnboardingView
            activeRepo={activeRepo}
            showToast={showToast}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="cyber-card p-6 font-mono text-xs flex flex-col sm:flex-row items-center justify-between gap-4 mt-8">
        <div className="flex items-center gap-2 text-black font-extrabold">
          <Terminal size={18} className="text-[var(--neon-pink)]" />
          <span>CODEMENTOR AI © 2026 // FASTAPI + QDRANT + QWEN RAG ENGINE</span>
        </div>

        <div className="flex items-center gap-4">
          <span className="cyber-badge cyber-badge-green text-xs font-black">
            LIGHT NEO-BRUTALIST
          </span>
          <a
            href="https://github.com/parinbajayebin/Codementor.ai"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 font-black text-black hover:text-[var(--neon-pink)] hover:underline text-xs bg-yellow-300 px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_#000]"
          >
            <GitBranch size={16} className="text-black" /> GITHUB REPO ↗
          </a>
        </div>
      </footer>

      {/* Toast Notifications */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}
