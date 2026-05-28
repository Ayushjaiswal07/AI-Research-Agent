// frontend/src/components/layout/Header.jsx

export default function Header() {
  return (
    <header className="flex items-center justify-between px-6 bg-gray-900 border-b border-gray-800 h-[60px]">
      <div className="flex items-center gap-2">
        <span className="text-xl font-bold text-white tracking-tight">⬡ Research</span>
        <span className="text-blue-500 font-mono text-xs border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 rounded-full">
          v1.0
        </span>
      </div>
      
      <div className="flex items-center gap-4">
        <select className="bg-gray-800 text-gray-400 text-xs font-mono px-3 py-1.5 rounded-md border border-gray-700 outline-none hover:border-gray-500 transition-colors">
          <option>gemini-2.5-flash</option>
        </select>
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500" />
      </div>
    </header>
  );
}