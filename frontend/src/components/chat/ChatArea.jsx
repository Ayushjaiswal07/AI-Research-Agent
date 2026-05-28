// frontend/src/components/chat/ChatArea.jsx
import { useEffect, useRef } from 'react';
import { useResearch } from '../../context/ResearchContext';
import MessageBubble from './MessageBubble';
import ThinkingBubble from './ThinkingBubble'; // Import the new component

export default function ChatArea() {
  const { messages, loading } = useResearch(); // Pull 'loading' from Context
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]); // Added loading to dependency to scroll when it appears

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
      {messages.length === 0 && !loading && (
        <div className="h-full flex flex-col items-center justify-center text-gray-500">
          <p className="text-xl font-semibold text-gray-400">How can I help you today?</p>
        </div>
      )}
      
      {messages.map((msg, idx) => (
        <MessageBubble key={idx} message={msg} />
      ))}

      {/* Conditionally render the thinking bubble */}
      {loading && <ThinkingBubble />}
    </div>
  );
}