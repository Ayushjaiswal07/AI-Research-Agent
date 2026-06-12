import { useResearch } from '../../context/ResearchContext';

const TOOL_SCORES = [
  { name: 'Ollama (Local)',  score: 95, color: 'bg-blue-500',   reason: 'Privacy + Zero Cost' },
  { name: 'ChromaDB',       score: 90, color: 'bg-purple-500',  reason: 'Vector Storage' },
  { name: 'DuckDuckGo',     score: 82, color: 'bg-teal-500',    reason: 'Web Search' },
  { name: 'MiniLM-L6-v2',  score: 88, color: 'bg-orange-400',  reason: 'Embeddings' },
];

export default function RightPanel() {
  const { sessionStats, uploadedFiles, selectedHashes } = useResearch();

  const doneFiles    = uploadedFiles.filter((f) => f.status === 'done');
  const totalChunks  = doneFiles.reduce((acc, f) => acc + (f.chunk_count || 0), 0);

  return (
    <aside className="bg-gray-900/60 border-l border-white/5 backdrop-blur-xl p-4 flex flex-col gap-6 w-[220px] overflow-y-auto">

      {/* ── Session Stats ────────────────────────────────────────────── */}
      <div>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-1">
          Session Stats
        </p>
        <div className="flex flex-col gap-2">
          <StatCard
            label="Queries"
            value={sessionStats.queries}
            sub="this session"
          />
          <StatCard
            label="Docs Indexed"
            value={`${totalChunks.toLocaleString()}`}
            sub={`${doneFiles.length} file${doneFiles.length !== 1 ? 's' : ''} uploaded`}
          />
          <StatCard
            label="Selected Files"
            value={selectedHashes.length === 0 ? 'All' : selectedHashes.length}
            sub={selectedHashes.length === 0 ? 'no filter active' : 'filter active'}
            highlight={selectedHashes.length > 0}
          />
        </div>
      </div>

      <div className="h-px bg-white/5" />

      {/* ── Tool Scores ──────────────────────────────────────────────── */}
      <div>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-1">
          Stack (RAG Fit)
        </p>
        <div className="flex flex-col gap-3">
          {TOOL_SCORES.map((tool) => (
            <div key={tool.name}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-300 font-medium truncate max-w-[120px]">{tool.name}</span>
                <span className="text-gray-500 font-mono shrink-0">{tool.score}%</span>
              </div>
              <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full ${tool.color} rounded-full transition-all duration-1000`}
                  style={{ width: `${tool.score}%` }}
                />
              </div>
              <p className="text-[10px] text-gray-600 mt-0.5">{tool.reason}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="h-px bg-white/5" />

      {/* ── Pipeline legend ──────────────────────────────────────────── */}
      <div>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-1">
          Intent Paths
        </p>
        <div className="flex flex-col gap-2 text-[11px] text-gray-500">
          {[
            { icon: '💬', label: 'Conversational', color: 'text-green-400' },
            { icon: '🧠', label: 'Brain (no retrieval)', color: 'text-purple-400' },
            { icon: '📂', label: 'Vector search', color: 'text-yellow-400' },
            { icon: '🌐', label: 'Web → RAG', color: 'text-sky-400' },
          ].map((p) => (
            <div key={p.label} className="flex items-center gap-2">
              <span>{p.icon}</span>
              <span className={p.color}>{p.label}</span>
            </div>
          ))}
        </div>
      </div>

    </aside>
  );
}

function StatCard({ label, value, sub, highlight = false }) {
  return (
    <div className={`rounded-lg px-3 py-2.5 border transition-colors
      ${highlight
        ? 'bg-blue-950/40 border-blue-700/40'
        : 'bg-gray-800/50 border-white/5'}`}
    >
      <p className={`text-base font-bold font-mono ${highlight ? 'text-blue-300' : 'text-white'}`}>
        {value}
      </p>
      <p className="text-[11px] text-gray-400 font-medium">{label}</p>
      {sub && <p className="text-[10px] text-gray-600 mt-0.5">{sub}</p>}
    </div>
  );
}
