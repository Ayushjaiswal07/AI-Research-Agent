import { useState } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import RightPanel from './components/layout/RightPanel';
import ChatArea from './components/chat/ChatArea';
import InputBar from './components/chat/InputBar';

export default function App() {
  const [rightOpen, setRightOpen] = useState(false);

  return (
    <div className="h-screen w-screen bg-gray-950 text-gray-200 flex flex-col overflow-hidden">

      {/* Header — passes toggle fn down */}
      <Header onToggleRight={() => setRightOpen((o) => !o)} rightOpen={rightOpen} />

      {/* Body */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* Left sidebar — fixed icon rail that expands on hover */}
        <Sidebar />

        {/* Main chat */}
        <main className="flex-1 flex flex-col overflow-hidden bg-gray-950 min-w-0">
          <ChatArea />
          <InputBar />
        </main>

        {/* Right panel — overlay drawer */}
        {rightOpen && (
          <>
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/40 z-20"
              onClick={() => setRightOpen(false)}
            />
            {/* Drawer */}
            <div className="absolute right-0 top-0 h-full w-[260px] z-30 bg-gray-900 border-l border-white/10 overflow-y-auto shadow-2xl">
              <RightPanel onClose={() => setRightOpen(false)} />
            </div>
          </>
        )}

      </div>
    </div>
  );
}
