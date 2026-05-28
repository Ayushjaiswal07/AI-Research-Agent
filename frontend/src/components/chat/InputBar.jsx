// frontend/src/components/chat/InputBar.jsx
import { useState } from 'react';
import { useResearch } from '../../context/ResearchContext';
import { ArrowUp } from 'lucide-react';

export default function InputBar() {
  const [input, setInput] = useState('');
  const { fetchResearch, loading } = useResearch();

  const handleSend = () => {
    if (!input.trim() || loading) return;
    fetchResearch(input);
    setInput('');
  };

  return (
    <div className="p-4 border-t border-gray-800 bg-gray-900">
      <div className="max-w-3xl mx-auto flex items-center gap-2 bg-gray-800 rounded-xl p-2 border border-gray-700 focus-within:border-blue-500 transition-all">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything..."
          className="flex-1 bg-transparent border-none outline-none text-white p-2 resize-none h-10"
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
        />
        <button 
          onClick={handleSend}
          disabled={loading}
          className="bg-blue-600 p-2 rounded-lg hover:bg-blue-500 disabled:opacity-50"
        >
          <ArrowUp size={20} />
        </button>
      </div>
    </div>
  );
}