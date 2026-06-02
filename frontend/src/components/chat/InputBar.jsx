// frontend/src/components/chat/InputBar.jsx
import { useState, useRef } from 'react';
import { useResearch } from '../../context/ResearchContext';
import { ArrowUp, Paperclip, X, FileText, Loader2 } from 'lucide-react';

const ACCEPTED_TYPES = ['application/pdf', 'text/plain'];
const ACCEPTED_EXT = ['.pdf', '.txt'];

export default function InputBar() {
  const [input, setInput] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [pendingFile, setPendingFile] = useState(null); // file staged before upload
  const fileInputRef = useRef(null);
  const { fetchResearch, uploadFile, loading } = useResearch();

  const isValidFile = (file) => {
    if (ACCEPTED_TYPES.includes(file.type)) return true;
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    return ACCEPTED_EXT.includes(ext);
  };

  const stageFile = (file) => {
    if (!file) return;
    if (!isValidFile(file)) {
      alert('Only PDF and plain-text (.txt) files are supported.');
      return;
    }
    setPendingFile(file);
  };

  const handleSend = () => {
    if (loading) return;

    // If a file is staged, upload it (optionally also send the text as a query)
    if (pendingFile) {
      uploadFile(pendingFile);
      setPendingFile(null);
      // If the user also typed something, send it as a follow-up research query
      if (input.trim()) {
        fetchResearch(input.trim());
        setInput('');
      }
      return;
    }

    if (!input.trim()) return;
    fetchResearch(input.trim());
    setInput('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    stageFile(file);
  };

  return (
    <div
      className={`p-4 border-t border-gray-800 bg-gray-900 transition-colors ${dragOver ? 'bg-gray-800' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Staged file chip */}
      {pendingFile && (
        <div className="max-w-3xl mx-auto mb-2 flex items-center gap-2 bg-blue-900/40 border border-blue-600/50 rounded-lg px-3 py-2 text-sm text-blue-200">
          <FileText size={15} className="shrink-0 text-blue-400" />
          <span className="flex-1 truncate">{pendingFile.name}</span>
          <span className="text-blue-400 text-xs shrink-0">
            {(pendingFile.size / 1024).toFixed(1)} KB
          </span>
          <button
            onClick={() => setPendingFile(null)}
            className="ml-1 text-blue-400 hover:text-white transition-colors"
            title="Remove file"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Drag-and-drop hint */}
      {dragOver && (
        <div className="max-w-3xl mx-auto mb-2 text-center text-blue-400 text-sm animate-pulse">
          Drop your PDF or .txt file here
        </div>
      )}

      <div className="max-w-3xl mx-auto flex items-center gap-2 bg-gray-800 rounded-xl p-2 border border-gray-700 focus-within:border-blue-500 transition-all">

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,application/pdf,text/plain"
          className="hidden"
          onChange={(e) => stageFile(e.target.files[0])}
        />

        {/* Paperclip button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          title="Attach a PDF or .txt file"
          className="text-gray-400 hover:text-blue-400 disabled:opacity-40 transition-colors p-1 rounded-lg"
        >
          <Paperclip size={20} />
        </button>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={pendingFile ? 'Add a question about this file, or just hit send to upload…' : 'Ask anything…'}
          className="flex-1 bg-transparent border-none outline-none text-white p-2 resize-none h-10"
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
        />

        <button
          onClick={handleSend}
          disabled={loading && !pendingFile}
          className="bg-blue-600 p-2 rounded-lg hover:bg-blue-500 disabled:opacity-50 transition-colors"
          title="Send"
        >
          {loading ? <Loader2 size={20} className="animate-spin" /> : <ArrowUp size={20} />}
        </button>
      </div>

      <p className="max-w-3xl mx-auto mt-1.5 text-xs text-gray-600 text-center">
        Attach a <strong className="text-gray-500">PDF</strong> or <strong className="text-gray-500">.txt</strong> file — it will be indexed and searchable in your next research query.
      </p>
    </div>
  );
}