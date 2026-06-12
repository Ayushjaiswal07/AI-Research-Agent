import { useResearch } from '../../context/ResearchContext';

export default function Header() {
  const { selectedHashes, uploadedFiles } = useResearch();
  const doneFiles = uploadedFiles.filter((f) => f.status === 'done');

  return (
    <header className="flex items-center justify-between px-6 bg-gray-900/80 backdrop-blur-xl border-b border-white/5 h-[60px] shrink-0">
      <div className="flex items-center gap-3">
        <span className="text-xl font-bold text-white tracking-tight">⬡ Research Agent</span>
        <span className="text-blue-500 font-mono text-xs border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 rounded-full">
          v1.0.0-stable
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* File selection indicator */}
        {selectedHashes.length > 0 && (
          <span className="text-xs text-blue-300 bg-blue-950/60 border border-blue-700/40 px-2.5 py-1 rounded-full">
            📌 {selectedHashes.length}/{doneFiles.length} file{selectedHashes.length !== 1 ? 's' : ''} selected
          </span>
        )}

        {/* Model badge — read from env, not a Gemini dropdown */}
        <div className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 px-3 py-1.5 rounded-md">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse shrink-0" />
          <span className="text-gray-300 text-xs font-mono">Ollama (local)</span>
        </div>

        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 shrink-0" />
      </div>
    </header>
  );
}
