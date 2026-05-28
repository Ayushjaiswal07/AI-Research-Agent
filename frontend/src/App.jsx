// frontend/src/App.jsx
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import RightPanel from './components/layout/RightPanel';
import ChatArea from './components/chat/ChatArea';
import InputBar from './components/chat/InputBar';

export default function App() {
  return (
    <div className="h-screen w-screen bg-gray-950 text-gray-200 grid grid-cols-[280px_1fr_320px] grid-rows-[60px_1fr] overflow-hidden">
      
      <div className="col-span-3">
        <Header />
      </div>

      <Sidebar />

      {/* Main Chat Area - Integrated */}
      <main className="border-r border-gray-800 bg-gray-950 flex flex-col h-full overflow-hidden">
        <ChatArea />
        <InputBar />
      </main>

      <RightPanel />

    </div>
  );
}