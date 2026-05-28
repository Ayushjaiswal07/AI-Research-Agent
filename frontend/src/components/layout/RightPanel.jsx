// frontend/src/components/layout/RightPanel.jsx
import StatCard from '../shared/StatCard';

const TOOLS = [
  { name: 'Gemini 2.5', score: 95, color: 'bg-blue-500' },
  { name: 'Claude 3.5', score: 88, color: 'bg-purple-500' },
  { name: 'GPT-4o', score: 82, color: 'bg-teal-500' },
];

export default function RightPanel() {
  return (
    <aside className="bg-gray-900 border-l border-gray-800 p-4 flex flex-col overflow-y-auto">
      {/* Session Stats */}
      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4 px-1">
        Session Stats
      </div>
      
      <StatCard label="Tokens Used" value="12,450" sub="~$0.012 estimated" />
      <StatCard label="Queries" value="4" sub="this session" />
      <StatCard label="Docs in RAG" value="128" sub="chunks indexed" />

      <div className="h-px bg-gray-800 my-6" />

      {/* Tool Comparison */}
      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4 px-1">
        Tool Scores (RAG Fit)
      </div>
      
      <div className="flex flex-col gap-3">
        {TOOLS.map((tool) => (
          <div key={tool.name}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-300 font-medium">{tool.name}</span>
              <span className="text-gray-500 font-mono">{tool.score}%</span>
            </div>
            <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
              <div 
                className={`h-full ${tool.color} rounded-full transition-all duration-1000`} 
                style={{ width: `${tool.score}%` }} 
              />
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}