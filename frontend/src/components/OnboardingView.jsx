import React, { useState } from 'react';
import { BookOpen, Copy, Check, Sparkles, Compass, FileText, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';

export default function OnboardingView({ activeRepo, showToast }) {
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    if (!activeRepo) { 
      showToast('Select a repo first', 'error'); 
      return; 
    }
    setLoading(true);
    try {
      const res = await api.searchChunks(activeRepo.repo_id, 'main entry point architecture setup routing');
      const files = res.results ? [...new Set(res.results.map(r => r.file_path))] : [];

      setGuide({
        title: `ONBOARDING GUIDE // ${activeRepo.repo_id.toUpperCase()}`,
        time: new Date().toISOString(),
        sections: [
          { heading: '1. EXECUTIVE OVERVIEW', content: `Repository ${activeRepo.repo_id} contains ${activeRepo.total_files || 'parsed'} source files indexed into ${activeRepo.total_chunks || 'multiple'} semantic chunks in Qdrant Vector DB.` },
          { heading: '2. KEY ENTRY POINTS', content: files.slice(0, 5).map(f => `• ${f}`).join('\n') || '• See ingested file tree for details' },
          { heading: '3. SYSTEM ARCHITECTURE', content: 'Modular structure with separated service layers. Uses fixed-size overlapping chunks for RAG contextual safety.' },
          { heading: '4. DEVELOPER GETTING STARTED', content: '1. Clone the repository\n2. Inspect key entry points listed above\n3. Use RAG Chat to ask specific code architecture questions.' },
        ],
      });
      showToast('Onboarding guide generated successfully!', 'success');
    } catch (err) { 
      showToast(err.message, 'error'); 
    } finally { 
      setLoading(false); 
    }
  };

  const copyGuide = () => {
    if (!guide) return;
    const md = `# ${guide.title}\n\n` + guide.sections.map(s => `## ${s.heading}\n${s.content}`).join('\n\n');
    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!activeRepo) {
    return (
      <div className="cyber-card p-12 text-center space-y-4">
        <ShieldAlert size={48} className="mx-auto text-[var(--neon-pink)]" />
        <h3 className="text-2xl font-black text-black">NO REPO SELECTED</h3>
        <p className="font-mono text-sm text-gray-700 font-bold">
          Select a repository from the INGEST tab to generate onboarding docs
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full">
      {/* Banner */}
      <div className="cyber-card cyber-card-pink p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight flex items-center gap-3 text-white">
            <BookOpen size={26} strokeWidth={3} /> DEVELOPER ONBOARDING GUIDE
          </h2>
          <p className="font-mono text-sm text-white/90 mt-1 font-bold">
            Auto-generate developer onboarding documentation for <strong>{activeRepo.repo_id}</strong>
          </p>
        </div>
        <button onClick={generate} disabled={loading} className="cyber-btn cyber-btn-yellow text-base py-3 px-6">
          <Sparkles size={18} className="text-black" /> {loading ? 'GENERATING...' : 'GENERATE GUIDE'}
        </button>
      </div>

      {guide ? (
        <div className="cyber-card p-6 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b-2 border-black">
            <h3 className="text-lg font-black font-mono text-black">{guide.title}</h3>
            <button onClick={copyGuide} className="cyber-btn cyber-btn-cyan text-xs py-1.5 px-3">
              {copied ? <Check size={14} className="text-black" /> : <Copy size={14} className="text-black" />}
              {copied ? 'COPIED!' : 'COPY MARKDOWN'}
            </button>
          </div>
          {guide.sections.map((s, i) => (
            <div key={i} className="p-5 border-2 border-black bg-white shadow-[4px_4px_0px_#000]">
              <h4 className="text-base font-black mb-2 flex items-center gap-2 font-mono text-black">
                <Compass size={18} className="text-[var(--neon-pink)]" /> {s.heading}
              </h4>
              <div className="text-sm leading-relaxed whitespace-pre-line font-sans text-black font-medium">
                {s.content}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="cyber-card p-12 text-center space-y-4">
          <FileText size={48} className="mx-auto text-[var(--neon-purple)]" />
          <h3 className="text-xl font-black font-mono text-black">CLICK GENERATE TO CREATE DOCS</h3>
        </div>
      )}
    </div>
  );
}
