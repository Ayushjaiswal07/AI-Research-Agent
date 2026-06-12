import { useEffect, useState } from 'react';
import { Microscope, FileText, Scale, Target, Upload, Loader2, Trash2, CheckSquare, Square, FileIcon } from 'lucide-react';
import { useResearch } from '../../context/ResearchContext';
import axios from 'axios';

const MODES = [
  { id: 'research', label: 'Deep Research', icon: Microscope },
  { id: 'summarize', label: 'Summarize', icon: FileText },
  { id: 'compare', label: 'Compare', icon: Scale },
  { id: 'extract', label: 'Extract Facts', icon: Target },
];

export default function Sidebar() {
  const {
    mode, setMode,
    uploadedFiles, refreshFiles,
    uploadFile, deleteFile,
    selectedHashes, toggleFileSelection,
  } = useResearch();

  const [uploading, setUploading] = useState(false);
  const [deletingHash, setDeletingHash] = useState(null);

  // Load files from backend when sidebar mounts
  useEffect(() => {
    refreshFiles();
  }, [refreshFiles]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setUploading(true);
    await uploadFile(file);
    await refreshFiles();
    setUploading(false);
    // Reset input so same file can be re-uploaded if needed
    event.target.value = '';
  };

  const handleDelete = async (url_hash, e) => {
    e.stopPropagation(); // don't trigger selection when clicking delete
    setDeletingHash(url_hash);
    await deleteFile(url_hash);
    setDeletingHash(null);
  };

  const doneFiles = uploadedFiles.filter((f) => f.status === 'done');
  const pendingFiles = uploadedFiles.filter((f) => f.status === 'uploading' || f.status === 'error');

  return (
    <aside className="border-r border-white/10 bg-gray-900/50 backdrop-blur-xl p-4 flex flex-col gap-6 w-[280px] h-full overflow-y-auto">

      {/* ── Research Modes ─────────────────────────────────────────────── */}
      <div>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-2">
          Research Mode
        </p>
        <div className="flex flex-col gap-1">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all w-full
                ${mode === m.id
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
            >
              <m.icon size={16} />
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-px bg-white/5" />

      {/* ── Documents Section ──────────────────────────────────────────── */}
      <div className="flex-grow flex flex-col gap-3">
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest px-2">
          Documents (RAG)
        </p>

        {/* Upload dropzone */}
        <label className={`
          border border-dashed border-white/10 rounded-lg p-4 text-center cursor-pointer
          hover:border-blue-500/50 hover:bg-blue-500/5 transition-all block
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}>
          <input
            type="file"
            className="hidden"
            onChange={handleFileUpload}
            disabled={uploading}
            accept=".pdf,.txt,.md"
          />
          {uploading ? (
            <Loader2 className="mx-auto mb-2 animate-spin text-blue-500" size={20} />
          ) : (
            <Upload className="mx-auto mb-2 text-gray-500" size={20} />
          )}
          <p className="text-xs text-gray-400">
            {uploading ? 'Indexing...' : 'Upload PDF / TXT / MD'}
          </p>
        </label>

        {/* Selection hint */}
        {doneFiles.length > 0 && (
          <p className="text-[10px] text-gray-600 px-1">
            {selectedHashes.length === 0
              ? 'Select files to restrict the LLM to those documents only.'
              : `${selectedHashes.length} file${selectedHashes.length > 1 ? 's' : ''} selected — LLM will only use these.`}
          </p>
        )}

        {/* Uploading / error in-progress entries */}
        {pendingFiles.map((f, i) => (
          <div
            key={`pending-${i}`}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/60 border border-white/5"
          >
            {f.status === 'uploading' ? (
              <Loader2 size={14} className="animate-spin text-blue-400 shrink-0" />
            ) : (
              <span className="text-red-400 text-xs shrink-0">✗</span>
            )}
            <span className="text-xs text-gray-400 truncate flex-1">{f.filename}</span>
            {f.status === 'error' && (
              <span className="text-[10px] text-red-400 shrink-0">failed</span>
            )}
          </div>
        ))}

        {/* Indexed file list */}
        {doneFiles.length === 0 && !uploading && (
          <p className="text-xs text-gray-600 text-center py-2">No documents uploaded yet.</p>
        )}

        <div className="flex flex-col gap-1">
          {doneFiles.map((f) => {
            const isSelected = selectedHashes.includes(f.url_hash);
            const isDeleting = deletingHash === f.url_hash;

            return (
              <div
                key={f.url_hash}
                onClick={() => toggleFileSelection(f.url_hash)}
                className={`
                  group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all
                  ${isSelected
                    ? 'bg-blue-600/20 border border-blue-500/40 text-blue-300'
                    : 'bg-gray-800/40 border border-white/5 text-gray-400 hover:bg-gray-800/70 hover:text-gray-200'}
                `}
              >
                {/* Checkbox icon */}
                <div className="shrink-0 text-blue-400">
                  {isSelected
                    ? <CheckSquare size={15} />
                    : <Square size={15} className="text-gray-600 group-hover:text-gray-400" />}
                </div>

                {/* File icon + name */}
                <FileIcon size={13} className="shrink-0 opacity-60" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs truncate">{f.filename}</p>
                  <p className="text-[10px] text-gray-600">{f.chunk_count} chunks</p>
                </div>

                {/* Delete button */}
                <button
                  onClick={(e) => handleDelete(f.url_hash, e)}
                  disabled={isDeleting}
                  title="Delete from knowledge base"
                  className="shrink-0 opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all disabled:opacity-40"
                >
                  {isDeleting
                    ? <Loader2 size={14} className="animate-spin" />
                    : <Trash2 size={14} />}
                </button>
              </div>
            );
          })}
        </div>

        {/* Clear selection button */}
        {selectedHashes.length > 0 && (
          <button
            onClick={() => selectedHashes.forEach(h => toggleFileSelection(h))}
            className="text-[11px] text-blue-500 hover:text-blue-400 transition-colors text-left px-1 mt-1"
          >
            ✕ Clear selection
          </button>
        )}
      </div>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <div className="text-[10px] text-gray-600 px-2 font-mono">
        v1.0.0-stable
      </div>
    </aside>
  );
}
