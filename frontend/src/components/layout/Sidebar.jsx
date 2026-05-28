import { useState } from 'react';
import { Microscope, FileText, Scale, Target, Upload, Loader2 } from 'lucide-react';
import { useResearch } from '../../context/ResearchContext';
import axios from 'axios';

const MODES = [
  { id: 'research', label: 'Deep Research', icon: Microscope },
  { id: 'summarize', label: 'Summarize', icon: FileText },
  { id: 'compare', label: 'Compare', icon: Scale },
  { id: 'extract', label: 'Extract Facts', icon: Target },
];

export default function Sidebar() {
  const { mode, setMode } = useResearch();
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/api/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      alert(`Success: ${response.data.message}`);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Check backend console for details.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <aside className="border-r border-white/10 bg-gray-900/50 backdrop-blur-xl p-4 flex flex-col gap-6 w-[280px] h-full">
      {/* 1. Research Modes Section */}
      <div>
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-2">
          Research Mode
        </p>
        <div className="flex flex-col gap-1">
          {MODES.map((m) => (
            <button 
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all w-full
                ${mode === m.id 
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
            >
              <m.icon size={16} />
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-px bg-white/5" />

      {/* 2. Documents Section */}
      <div className="flex-grow">
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 px-2">
          Documents (RAG)
        </p>
        
        <label className={`
          border border-dashed border-white/10 rounded-lg p-4 text-center cursor-pointer 
          hover:border-blue-500/50 hover:bg-blue-500/5 transition-all block
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}>
          <input 
            type="file" 
            className="hidden" 
            onChange={handleFileUpload} 
            disabled={uploading}
            accept=".pdf,.txt,.md" 
          />
          {uploading ? (
            <Loader2 className="mx-auto mb-2 animate-spin text-blue-500" size={20} />
          ) : (
            <Upload className="mx-auto mb-2 text-gray-500" size={20} />
          )}
          <p className="text-xs text-gray-400">
            {uploading ? "Indexing..." : "Upload PDF / TXT / MD"}
          </p>
        </label>
      </div>

      {/* 3. Footer / Version Info */}
      <div className="text-[10px] text-gray-600 px-2 font-mono">
        v1.0.0-stable
      </div>
    </aside>
  );
}