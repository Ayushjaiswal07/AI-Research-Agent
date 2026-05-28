// frontend/src/components/chat/MessageBubble.jsx
import ReactMarkdown from 'react-markdown';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[70%] p-4 rounded-2xl ${
        isUser 
          ? 'bg-blue-600 text-white rounded-br-none' 
          : 'bg-gray-800 text-gray-200 rounded-bl-none border border-gray-700'
      }`}>
        {/* WRAP IN A DIV INSTEAD OF PASSING CLASSNAME TO REACTMARKDOWN */}
        <div className="prose prose-invert prose-sm">
          <ReactMarkdown>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}