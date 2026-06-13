import { Menu, X } from 'lucide-react';
import { useResearch } from '../../context/ResearchContext';

export default function Header({ onToggleRight, rightOpen }) {
  const { selectedHashes, uploadedFiles } = useResearch();
  const doneFiles = uploadedFiles.filter((f) => f.status === 'done');

  return (
    <header className="flex items-center justify-between px-4 bg-gray-900/80 backdrop-blur-xl border-b border-white/5 h-[56px] shrink-0 z-10">

      {/* Left — logo */}
      <div className="flex items-center gap-2.5">
        <span className="text-lg font-bold text-white tracking-tight">⬡ Research Agent</span>
        <span className="text-blue-500 font-mono text-[11px] border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 rounded-full hidden sm:inline">
          v1.0.0
        </span>
      </div>

      {/* Right — status + hamburger */}
      <div className="flex items-center gap-2">

        {/* File selection pill */}
        {selectedHashes.length > 0 && (
          <span className="text-xs text-blue-300 bg-blue-950/60 border border-blue-700/40 px-2.5 py-1 rounded-full hidden sm:inline-flex items-center gap-1">
            📌 {selectedHashes.length}/{doneFiles.length} selected
          </span>
        )}

        {/* Ollama status badge */}
        <div className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 px-2.5 py-1.5 rounded-md">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse shrink-0" />
          <span className="text-gray-300 text-xs font-mono hidden sm:inline">Ollama</span>
        </div>

        {/* Hamburger — toggles right panel */}
        <button
          onClick={onToggleRight}
          className={`p-2 rounded-lg border transition-all ${
            rightOpen
              ? 'bg-blue-600/20 border-blue-500/40 text-blue-400'
              : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
          title={rightOpen ? 'Close info panel' : 'Open info panel'}
        >
          {rightOpen ? <X size={16} /> : <Menu size={16} />}
        </button>
      </div>
    </header>
  );
}
