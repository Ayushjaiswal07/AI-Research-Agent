// frontend/src/components/chat/ThinkingBubble.jsx
export default function ThinkingBubble() {
  return (
    <div className="flex justify-start">
      <div className="bg-gray-800 text-gray-400 p-4 rounded-2xl rounded-bl-none border border-gray-700 flex items-center gap-2">
        {/* Three animated dots */}
        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
        <span className="ml-2 text-sm italic"></span>
      </div>
    </div>
  );
}