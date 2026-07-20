import React, { useState } from 'react';
import { 
  Play, 
  Loader2, 
  Trash2, 
  ArrowRight, 
  CheckCircle2, 
  FolderGit2, 
  Database, 
  Zap,
  GitPullRequest,
  Cpu
} from 'lucide-react';
import { api } from '../services/api';

const PRESETS = [
  { name: 'pallets/flask', url: 'https://github.com/pallets/flask', lang: 'Python' },
  { name: 'expressjs/express', url: 'https://github.com/expressjs/express', lang: 'JavaScript' },
  { name: 'fastapi/fastapi', url: 'https://github.com/fastapi/fastapi', lang: 'Python' },
];

export default function IngestView({ 
  repos, 
  fetchRepos, 
  setActiveRepo, 
  setTab, 
  showToast 
}) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);

  const steps = [
    'Git Shallow Clone Repo',
    'Recursive Source Parsing & Filtering',
    'Overlapping Chunking & Local Embeddings (bge-small-en-v1.5)',
    'Qdrant Vector DB Payload Indexing'
  ];

  const handleIngest = async (targetUrl = url) => {
    const trimmed = targetUrl.trim();
    if (!trimmed) {
      showToast('Please enter a GitHub repository URL', 'error');
      return;
    }

    setLoading(true);
    setStep(1);

    const t1 = setTimeout(() => setStep(2), 2500);
    const t2 = setTimeout(() => setStep(3), 5000);
    const t3 = setTimeout(() => setStep(4), 7500);

    try {
      const res = await api.ingestRepo(trimmed);
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);

      setStep(5);
      showToast(`Repository '${res.repo_id}' ingested successfully!`, 'success');
      await fetchRepos();
      setActiveRepo({ 
        repo_id: res.repo_id, 
        total_files: res.total_files, 
        total_chunks: res.total_chunks, 
        status: 'completed' 
      });
    } catch (err) {
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
      showToast(`Ingestion failed: ${err.message}`, 'error');
      setStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (repoId) => {
    if (!confirm(`Are you sure you want to delete '${repoId}' and all its vectors?`)) return;
    try {
      await api.deleteRepo(repoId);
      showToast(`Repository '${repoId}' deleted`, 'success');
      await fetchRepos();
    } catch (err) {
      showToast(`Delete failed: ${err.message}`, 'error');
    }
  };

  return (
    <div className="w-full flex flex-col">
      
      {/* CARD 1: Hero Banner */}
      <div 
        className="cyber-card cyber-card-yellow p-6 lg:p-8"
        style={{ marginBottom: '27px' }}
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <h2 className="text-2xl lg:text-3xl font-black tracking-tight text-black flex items-center gap-3">
              <Zap size={32} className="text-black" />
              CODEBASE INGESTION PIPELINE
            </h2>
            <p className="font-mono text-sm text-gray-900 font-bold mt-3 max-w-4xl leading-relaxed">
              Clone any public GitHub codebase. The system parses source code files, splits them into overlapping 
              chunks, generates 384-dimensional embeddings via local <strong>BAAI/bge-small-en-v1.5</strong>, 
              and indexes vectors in <strong>Qdrant Cloud</strong>.
            </p>
          </div>
          <span className="cyber-badge cyber-badge-green text-xs px-4 py-2 self-start lg:self-center shrink-0">
            VECTOR INDEX READY ⚡
          </span>
        </div>
      </div>

      {/* CARD 2: Ingest Form */}
      <div 
        className="cyber-card p-6 lg:p-8 space-y-6"
        style={{ marginBottom: '27px' }}
      >
        <h3 className="text-xl font-black flex items-center gap-3 text-black">
          <FolderGit2 className="text-[var(--neon-pink)]" />
          INGEST NEW REPOSITORY
        </h3>

        <div className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            placeholder="https://github.com/username/repository"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleIngest()}
            disabled={loading}
            className="cyber-input flex-1 text-base py-3.5"
          />
          <button
            onClick={() => handleIngest()}
            disabled={loading}
            className="cyber-btn cyber-btn-green text-base py-3.5 px-8 whitespace-nowrap"
          >
            {loading ? <Loader2 size={20} className="animate-spin text-black" /> : <Play size={20} className="text-black" />}
            {loading ? 'INGESTING...' : 'START INGESTION'}
          </button>
        </div>
      </div>

      {/* CARD 3: Quick Test Presets */}
      <div 
        className="cyber-card p-6 lg:p-8 space-y-4"
        style={{ marginBottom: '27px' }}
      >
        <span className="font-mono text-xs font-black text-black block uppercase tracking-wider flex items-center gap-2">
          <GitPullRequest size={16} className="text-[var(--neon-pink)]" /> QUICK TEST PRESETS:
        </span>
        <div className="flex flex-wrap gap-4">
          {PRESETS.map((preset) => (
            <button
              key={preset.name}
              onClick={() => {
                setUrl(preset.url);
                handleIngest(preset.url);
              }}
              disabled={loading}
              className="cyber-btn text-xs py-3 px-6 bg-white hover:bg-yellow-100"
            >
              <GitPullRequest size={16} className="text-[var(--neon-purple)]" />
              {preset.name} ({preset.lang})
            </button>
          ))}
        </div>
      </div>

      {/* CARD 4 & 5: Pipeline Monitor + Ingested Repos Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Pipeline Step Monitor Card */}
        <div 
          className="cyber-card p-6 lg:p-8 space-y-6"
          style={{ marginBottom: '27px' }}
        >
          <h3 className="text-lg font-black flex items-center gap-3 text-black">
            <Cpu className="text-[var(--neon-cyan)]" />
            PIPELINE STEP MONITOR
          </h3>

          <div className="space-y-4 font-mono text-xs">
            {steps.map((s, i) => {
              const stepNum = i + 1;
              const active = step === stepNum;
              const done = step > stepNum;
              const stepColors = ['#ffdd00', '#00d2ff', '#ff2a75', '#00e659'];

              return (
                <div
                  key={i}
                  className="p-4 border-2 border-black transition-all flex items-center justify-between font-black shadow-[3px_3px_0px_#000]"
                  style={{
                    background: (active || done) ? stepColors[i] : 'white',
                    color: '#000000',
                  }}
                >
                  <span>{stepNum}. {s}</span>
                  {active && <Loader2 size={18} className="animate-spin text-black" />}
                  {done && <CheckCircle2 size={18} className="text-black" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Ingested Repositories List Table */}
        <div 
          className="lg:col-span-2 cyber-card p-6 lg:p-8 space-y-6"
          style={{ marginBottom: '27px' }}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-black flex items-center gap-3 text-black">
              <Database className="text-[var(--neon-green)]" />
              INGESTED REPOSITORIES ({repos ? repos.length : 0})
            </h3>
            <button
              onClick={fetchRepos}
              className="cyber-btn text-xs py-2 px-4"
            >
              REFRESH
            </button>
          </div>

          {(!repos || repos.length === 0) ? (
            <div className="p-12 text-center border-2 border-dashed border-black font-mono text-sm text-gray-800 font-bold bg-white">
              No repositories ingested yet. Use the form above or click a preset to start!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs border-collapse">
                <thead>
                  <tr className="border-b-2 border-black bg-yellow-200 text-black">
                    <th className="p-4 font-black">REPO ID</th>
                    <th className="p-4 font-black">FILES</th>
                    <th className="p-4 font-black">CHUNKS</th>
                    <th className="p-4 font-black">STATUS</th>
                    <th className="p-4 font-black text-right">ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {repos.map((repo) => (
                    <tr key={repo.repo_id} className="border-b border-black hover:bg-yellow-50 text-black">
                      <td className="p-4 font-black text-black flex items-center gap-2">
                        <FolderGit2 size={18} className="text-[var(--neon-purple)]" />
                        {repo.repo_id}
                      </td>
                      <td className="p-4 font-bold text-gray-800">{repo.total_files || '—'} files</td>
                      <td className="p-4 font-black text-purple-700">
                        {repo.total_chunks || '—'} chunks
                      </td>
                      <td className="p-4">
                        <span className="cyber-badge cyber-badge-green">
                          READY ⚡
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-3">
                          <button
                            onClick={() => {
                              setActiveRepo(repo);
                              setTab('chat');
                              showToast(`Selected '${repo.repo_id}' for RAG Chat`, 'info');
                            }}
                            className="cyber-btn cyber-btn-cyan text-xs py-2 px-4"
                          >
                            CHAT <ArrowRight size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(repo.repo_id)}
                            className="cyber-btn cyber-btn-pink text-xs py-2 px-3"
                            title="Delete Repo Vectors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
