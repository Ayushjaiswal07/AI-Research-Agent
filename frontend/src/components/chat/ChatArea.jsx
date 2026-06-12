import { useEffect, useRef } from 'react';
import { useResearch } from '../../context/ResearchContext';
import MessageBubble from './MessageBubble';
import ThinkingBubble from './ThinkingBubble';

export default function ChatArea() {
  const { messages, loading, thinkingSteps } = useResearch();
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading, thinkingSteps]);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
      {messages.length === 0 && !loading && (
        <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-3">
          <div className="text-5xl">⬡</div>
          <p className="text-xl font-semibold text-gray-400">How can I help you today?</p>
          <p className="text-sm text-gray-600">Ask anything, upload a document, or select files from the sidebar.</p>
        </div>
      )}

      {messages.map((msg, idx) => (
        <MessageBubble key={idx} message={msg} />
      ))}

      {/* Live thinking bubble — shows while loading */}
      {loading && <ThinkingBubble steps={thinkingSteps} />}
    </div>
  );
}
