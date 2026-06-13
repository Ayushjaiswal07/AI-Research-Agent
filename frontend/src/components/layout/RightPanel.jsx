import { X, Trash2, Clock } from 'lucide-react';
import { useResearch } from '../../context/ResearchContext';

const TOOL_SCORES = [
  { name: 'Ollama (Local)', score: 95, color: 'bg-blue-500',   reason: 'Privacy + Zero Cost' },
  { name: 'ChromaDB',       score: 90, color: 'bg-purple-500', reason: 'Vector Storage'      },
  { name: 'DuckDuckGo',     score: 82, color: 'bg-teal-500',   reason: 'Web Search'          },
  { name: 'MiniLM-L6-v2',  score: 88, color: 'bg-orange-400', reason: 'Embeddings'          },
];

const INTENT_PATHS = [
  { icon: '💬', label: 'Conversational',       color: 'text-green-400'  },
  { icon: '🧠', label: 'Brain (no retrieval)', color: 'text-purple-400' },
  { icon: '📂', label: 'Vector search',         color: 'text-yellow-400' },
  { icon: '🌐', label: 'Web → RAG',             color: 'text-sky-400'    },
];

function formatTs(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

export default function RightPanel({ onClose }) {
  const {
    sessionStats, uploadedFiles, selectedHashes,
    chatHistory, clearHistory,
  } = useResearch();

  const doneFiles   = uploadedFiles.filter((f) => f.status === 'done');
  const totalChunks = doneFiles.reduce((acc, f) => acc + (f.chunk_count || 0), 0);

  // Show most recent first
  const recentHistory = [...chatHistory].reverse().slice(0, 30);

  return (
    <div className="flex flex-col h-full p-4 gap-5 overflow-y-auto">

      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <p className="text-sm font-semibold text-gray-200">Agent Info</p>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-white transition-colors p-1 rounded-md hover:bg-white/10"
        >
          <X size={16} />
        </button>
      </div>

      {/* Session Stats */}
      <section>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 px-1">
          Session Stats
        </p>
        <div className="flex flex-col gap-2">
          <StatCard label="Queries"        value={sessionStats.queries}          sub="this session" />
          <StatCard label="Chunks Indexed" value={totalChunks.toLocaleString()}  sub={`${doneFiles.length} file${doneFiles.length !== 1 ? 's' : ''}`} />
          <StatCard
            label="File Filter"
            value={selectedHashes.length === 0 ? 'All docs' : `${selectedHashes.length} selected`}
            sub={selectedHashes.length === 0 ? 'no filter active' : 'web search disabled'}
            highlight={selectedHashes.length > 0}
          />
        </div>
      </section>

      <div className="h-px bg-white/5 shrink-0" />

      {/* Chat History */}
      <section className="flex flex-col gap-2 min-h-0">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest px-1">
            Chat History ({chatHistory.length})
          </p>
          {chatHistory.length > 0 && (
            <button
              onClick={clearHistory}
              title="Clear all history"
              className="text-gray-600 hover:text-red-400 transition-colors"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>

        {recentHistory.length === 0 ? (
          <p className="text-[11px] text-gray-600 px-1">No history yet. Ask something!</p>
        ) : (
          <div className="flex flex-col gap-1.5 overflow-y-auto max-h-64">
            {recentHistory.map((entry) => (
              <div
                key={entry.id}
                className="bg-gray-800/50 border border-white/5 rounded-lg px-3 py-2"
              >
                <div className="flex items-center gap-1 mb-1">
                  <Clock size={10} className="text-gray-600 shrink-0" />
                  <span className="text-[10px] text-gray-600 font-mono">
                    {formatTs(entry.timestamp)}
                  </span>
                </div>
                <p className="text-[11px] text-gray-300 font-medium truncate" title={entry.topic}>
                  {entry.topic}
                </p>
                <p className="text-[10px] text-gray-500 mt-0.5 line-clamp-2">
                  {entry.summary}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="h-px bg-white/5 shrink-0" />

      {/* Stack scores */}
      <section>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 px-1">
          Stack (RAG Fit)
        </p>
        <div className="flex flex-col gap-3">
          {TOOL_SCORES.map((tool) => (
            <div key={tool.name}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-300 font-medium truncate">{tool.name}</span>
                <span className="text-gray-500 font-mono shrink-0">{tool.score}%</span>
              </div>
              <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                <div className={`h-full ${tool.color} rounded-full`} style={{ width: `${tool.score}%` }} />
              </div>
              <p className="text-[10px] text-gray-600 mt-0.5">{tool.reason}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="h-px bg-white/5 shrink-0" />

      {/* Intent paths */}
      <section>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2 px-1">
          Intent Routing
        </p>
        <div className="flex flex-col gap-2">
          {INTENT_PATHS.map((p) => (
            <div key={p.label} className="flex items-center gap-2 text-[11px]">
              <span>{p.icon}</span>
              <span className={p.color}>{p.label}</span>
            </div>
          ))}
        </div>
      </section>

      <div className="mt-auto text-[10px] text-gray-600 font-mono border-t border-white/5 pt-3 shrink-0">
        v1.0.0-stable · Ollama local
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, highlight = false }) {
  return (
    <div className={`rounded-lg px-3 py-2.5 border ${highlight ? 'bg-blue-950/40 border-blue-700/40' : 'bg-gray-800/50 border-white/5'}`}>
      <p className={`text-base font-bold font-mono ${highlight ? 'text-blue-300' : 'text-white'}`}>{value}</p>
      <p className="text-[11px] text-gray-400 font-medium">{label}</p>
      {sub && <p className="text-[10px] text-gray-600 mt-0.5">{sub}</p>}
    </div>
  );
}
