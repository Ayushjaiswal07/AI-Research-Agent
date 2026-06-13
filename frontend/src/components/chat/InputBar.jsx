import { useState, useRef } from 'react';
import { useResearch } from '../../context/ResearchContext';
import { ArrowUp, Paperclip, X, FileText, Loader2, Globe, FolderOpen, Sparkles } from 'lucide-react';

const ACCEPTED_TYPES = ['application/pdf', 'text/plain'];
const ACCEPTED_EXT   = ['.pdf', '.txt'];

const SOURCE_OPTIONS = [
  {
    id: 'auto',
    label: 'Auto',
    icon: Sparkles,
    desc: 'Let the agent decide',
    activeClass: 'bg-gray-700 text-white border-gray-500',
    inactiveClass: 'text-gray-500 border-gray-700 hover:border-gray-500 hover:text-gray-300',
  },
  {
    id: 'web',
    label: 'Web',
    icon: Globe,
    desc: 'Search the web',
    activeClass: 'bg-sky-600/30 text-sky-300 border-sky-500',
    inactiveClass: 'text-gray-500 border-gray-700 hover:border-sky-600 hover:text-sky-400',
  },
  {
    id: 'file',
    label: 'Files',
    icon: FolderOpen,
    desc: 'Use uploaded docs only',
    activeClass: 'bg-yellow-600/20 text-yellow-300 border-yellow-500',
    inactiveClass: 'text-gray-500 border-gray-700 hover:border-yellow-600 hover:text-yellow-400',
  },
  {
    id: 'both',
    label: 'Web + Files',
    icon: null, // rendered manually
    desc: 'Use both sources',
    activeClass: 'bg-purple-600/20 text-purple-300 border-purple-500',
    inactiveClass: 'text-gray-500 border-gray-700 hover:border-purple-500 hover:text-purple-400',
  },
];

export default function InputBar() {
  const [input, setInput]           = useState('');
  const [dragOver, setDragOver]     = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const fileInputRef = useRef(null);

  const { fetchResearch, uploadFile, loading, selectedHashes, sourceMode, setSourceMode } = useResearch();

  const isValidFile = (file) => {
    if (ACCEPTED_TYPES.includes(file.type)) return true;
    return ACCEPTED_EXT.includes('.' + file.name.split('.').pop().toLowerCase());
  };

  const stageFile = (file) => {
    if (!file) return;
    if (!isValidFile(file)) { alert('Only PDF and .txt files are supported.'); return; }
    setPendingFile(file);
  };

  const handleSend = () => {
    if (loading) return;
    if (pendingFile) {
      uploadFile(pendingFile);
      setPendingFile(null);
      if (input.trim()) { fetchResearch(input.trim()); setInput(''); }
      return;
    }
    if (!input.trim()) return;
    fetchResearch(input.trim());
    setInput('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    stageFile(e.dataTransfer.files[0]);
  };

  const activeSrc = SOURCE_OPTIONS.find((o) => o.id === sourceMode);

  // Dynamic placeholder
  const placeholder =
    pendingFile       ? 'Add a question about this file, or hit send to upload…'
    : sourceMode === 'web'  ? 'Ask anything — will search the web…'
    : sourceMode === 'file' ? 'Ask about your uploaded documents…'
    : sourceMode === 'both' ? 'Ask anything — will use web + your files…'
    : selectedHashes.length > 0 ? `Ask about ${selectedHashes.length} selected file${selectedHashes.length > 1 ? 's' : ''}…`
    : 'Ask anything…';

  return (
    <div
      className={`px-4 pt-2 pb-4 border-t border-gray-800 bg-gray-900/95 transition-colors ${dragOver ? 'bg-gray-800' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      {/* ── Source mode toggle bar ──────────────────────────────────── */}
      <div className="max-w-3xl mx-auto flex items-center gap-2 mb-2.5">
        <span className="text-[10px] text-gray-600 uppercase tracking-widest shrink-0 font-semibold">Source</span>
        <div className="flex items-center gap-1.5 flex-wrap">
          {SOURCE_OPTIONS.map((opt) => {
            const isActive = sourceMode === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => setSourceMode(opt.id)}
                title={opt.desc}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all
                  ${isActive ? opt.activeClass : opt.inactiveClass}`}
              >
                {opt.id === 'both' ? (
                  <span className="flex items-center gap-0.5">
                    <Globe size={11} />
                    <span className="text-[10px]">+</span>
                    <FolderOpen size={11} />
                  </span>
                ) : opt.icon ? (
                  <opt.icon size={12} />
                ) : null}
                {opt.label}
              </button>
            );
          })}
        </div>

        {/* Active mode hint */}
        <span className="ml-auto text-[10px] text-gray-600 shrink-0 hidden sm:inline">
          {activeSrc?.desc}
        </span>
      </div>

      {/* ── File selection banner ───────────────────────────────────── */}
      {selectedHashes.length > 0 && sourceMode === 'auto' && (
        <div className="max-w-3xl mx-auto mb-2 flex items-center gap-2 bg-yellow-950/40 border border-yellow-700/40 rounded-lg px-3 py-1.5 text-xs text-yellow-300">
          <span>📂</span>
          <span>
            <strong>{selectedHashes.length}</strong> file{selectedHashes.length > 1 ? 's' : ''} selected in sidebar — agent may use them.
          </span>
        </div>
      )}

      {/* ── Pending file chip ───────────────────────────────────────── */}
      {pendingFile && (
        <div className="max-w-3xl mx-auto mb-2 flex items-center gap-2 bg-blue-900/40 border border-blue-600/50 rounded-lg px-3 py-2 text-sm text-blue-200">
          <FileText size={14} className="shrink-0 text-blue-400" />
          <span className="flex-1 truncate text-xs">{pendingFile.name}</span>
          <span className="text-blue-400 text-[10px] shrink-0">{(pendingFile.size / 1024).toFixed(1)} KB</span>
          <button onClick={() => setPendingFile(null)} className="text-blue-400 hover:text-white transition-colors">
            <X size={13} />
          </button>
        </div>
      )}

      {dragOver && (
        <div className="max-w-3xl mx-auto mb-2 text-center text-blue-400 text-sm animate-pulse">
          Drop your PDF or .txt here
        </div>
      )}

      {/* ── Input row ───────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto flex items-center gap-2 bg-gray-800 rounded-xl p-2 border border-gray-700 focus-within:border-blue-500 transition-all">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,application/pdf,text/plain"
          className="hidden"
          onChange={(e) => stageFile(e.target.files[0])}
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          title="Attach a PDF or .txt file"
          className="text-gray-400 hover:text-blue-400 disabled:opacity-40 transition-colors p-1 rounded-lg shrink-0"
        >
          <Paperclip size={18} />
        </button>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          rows={1}
          className="flex-1 bg-transparent border-none outline-none text-white text-sm p-1 resize-none leading-6 min-h-[28px] max-h-32 overflow-y-auto"
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
          onInput={(e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px';
          }}
        />

        <button
          onClick={handleSend}
          disabled={loading}
          className="bg-blue-600 p-2 rounded-lg hover:bg-blue-500 disabled:opacity-50 transition-colors shrink-0"
          title="Send"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <ArrowUp size={18} />}
        </button>
      </div>

      {/* ── Footer hint ─────────────────────────────────────────────── */}
      <p className="max-w-3xl mx-auto mt-1.5 text-[10px] text-gray-600 text-center">
        {sourceMode === 'auto'
          ? 'Auto mode — agent decides whether to search the web, use files, or answer from knowledge.'
          : sourceMode === 'web'
          ? 'Web mode — will always search the web, ignoring uploaded files.'
          : sourceMode === 'file'
          ? 'File mode — will only read from uploaded documents, no web search.'
          : 'Both mode — will search the web AND read from uploaded documents.'}
      </p>
    </div>
  );
}
