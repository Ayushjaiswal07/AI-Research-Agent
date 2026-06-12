import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';

// Map step text prefixes to icon + colour
const STEP_META = [
  { match: '🚀', color: 'text-blue-400' },
  { match: '💬', color: 'text-green-400' },
  { match: '🧠', color: 'text-purple-400' },
  { match: '📂', color: 'text-yellow-400' },
  { match: '✅', color: 'text-green-400' },
  { match: '🔍', color: 'text-cyan-400' },
  { match: '🌐', color: 'text-sky-400' },
  { match: '↳',  color: 'text-gray-400' },
  { match: '📚', color: 'text-orange-400' },
  { match: '📊', color: 'text-indigo-400' },
  { match: '📝', color: 'text-violet-400' },
  { match: '✍️', color: 'text-pink-400' },
  { match: '⚙️', color: 'text-gray-300' },
  { match: '⚠️', color: 'text-amber-400' },
  { match: '❌', color: 'text-red-400' },
];

function stepColor(text) {
  for (const { match, color } of STEP_META) {
    if (text.startsWith(match)) return color;
  }
  return 'text-gray-400';
}

export default function ThinkingBubble({ steps = [] }) {
  const bottomRef = useRef(null);

  // Auto-scroll inside the thinking log as new steps arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [steps]);

  const latestStep = steps[steps.length - 1]?.text || 'Initialising...';

  return (
    <div className="flex justify-start w-full">
      <div className="w-full max-w-2xl bg-gray-900 border border-gray-700/60 rounded-2xl rounded-bl-none overflow-hidden shadow-xl">

        {/* ── Header bar ─────────────────────────────────────────────── */}
        <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-800/80 border-b border-gray-700/50">
          <Loader2 size={14} className="animate-spin text-blue-400 shrink-0" />
          <span className="text-xs font-semibold text-blue-300 tracking-wide uppercase">
            Agent Working
          </span>
          <span className="ml-auto text-[10px] text-gray-500 font-mono">
            {steps.length} step{steps.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* ── Step log ───────────────────────────────────────────────── */}
        {steps.length > 0 && (
          <div className="max-h-56 overflow-y-auto px-4 py-3 space-y-1.5 font-mono text-[12px] leading-relaxed">
            {steps.map((step, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 transition-opacity duration-300 ${
                  i === steps.length - 1 ? 'opacity-100' : 'opacity-50'
                }`}
              >
                {/* Timeline dot */}
                <span className="mt-1 shrink-0">
                  {i === steps.length - 1 ? (
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                  ) : (
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-600" />
                  )}
                </span>
                <span className={stepColor(step.text)}>{step.text}</span>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}

        {/* ── Current status bar ─────────────────────────────────────── */}
        <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-800/40 border-t border-gray-700/30">
          {/* Animated progress bar */}
          <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 rounded-full animate-[shimmer_2s_linear_infinite] bg-[length:200%_100%]" />
          </div>
          <span className="text-[11px] text-gray-500 truncate max-w-[60%] text-right">
            {latestStep.replace(/^[^\w\s]*\s*/, '')}
          </span>
        </div>
      </div>
    </div>
  );
}
