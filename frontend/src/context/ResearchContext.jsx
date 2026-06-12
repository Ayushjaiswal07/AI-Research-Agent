import { createContext, useContext, useState, useCallback, useRef } from 'react';
import axios from 'axios';

const ResearchContext = createContext(null);
const API_BASE = 'http://localhost:8000/api';

export const ResearchProvider = ({ children }) => {
  const [messages, setMessages]             = useState([]);
  const [loading, setLoading]               = useState(false);
  const [thinkingSteps, setThinkingSteps]   = useState([]);   // live step log
  const [mode, setMode]                     = useState('research');
  const [uploadedFiles, setUploadedFiles]   = useState([]);
  const [selectedHashes, setSelectedHashes] = useState([]);
  const [sessionStats, setSessionStats]     = useState({ queries: 0, chunks: 0 });

  const refreshFiles = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/files`);
      const files = res.data.map((f) => ({ ...f, status: 'done' }));
      setUploadedFiles(files);
      const totalChunks = files.reduce((acc, f) => acc + (f.chunk_count || 0), 0);
      setSessionStats((prev) => ({ ...prev, chunks: totalChunks }));
    } catch (err) {
      console.error('Failed to fetch file list:', err);
    }
  }, []);

  const uploadFile = async (file) => {
    const tempEntry = { filename: file.name, url_hash: null, chunk_count: null, status: 'uploading' };
    setUploadedFiles((prev) => [...prev, tempEntry]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { chunks_indexed, url_hash, filename } = res.data;
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.filename === file.name && f.status === 'uploading'
            ? { filename, url_hash, chunk_count: chunks_indexed, status: 'done' }
            : f
        )
      );
      setSessionStats((prev) => ({ ...prev, chunks: prev.chunks + chunks_indexed }));
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `📄 **File uploaded:** \`${filename}\` — ${chunks_indexed} chunks indexed. Select it in the sidebar to query it.`,
        },
      ]);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.filename === file.name && f.status === 'uploading' ? { ...f, status: 'error' } : f
        )
      );
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `❌ **Upload failed for \`${file.name}\`:** ${detail}` },
      ]);
    }
  };

  const deleteFile = async (url_hash) => {
    try {
      await axios.delete(`${API_BASE}/files/${url_hash}`);
      setUploadedFiles((prev) => prev.filter((f) => f.url_hash !== url_hash));
      setSelectedHashes((prev) => prev.filter((h) => h !== url_hash));
    } catch (err) {
      console.error('Failed to delete file:', err);
      alert('Failed to delete file. Check backend console.');
    }
  };

  const toggleFileSelection = (url_hash) => {
    setSelectedHashes((prev) =>
      prev.includes(url_hash) ? prev.filter((h) => h !== url_hash) : [...prev, url_hash]
    );
  };

  const fetchResearch = async (topic) => {
    setMessages((prev) => [...prev, { role: 'user', content: topic }]);
    setLoading(true);
    setThinkingSteps([]);

    try {
      const payload = {
        topic,
        selected_file_hashes: selectedHashes.length > 0 ? selectedHashes : null,
      };

      const response = await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Backend error');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete line in buffer

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const event = JSON.parse(raw);

            if (event.type === 'step') {
              setThinkingSteps((prev) => [...prev, { text: event.text, ts: Date.now() }]);
            } else if (event.type === 'report') {
              setThinkingSteps([]);
              setMessages((prev) => [...prev, { role: 'assistant', content: event.text }]);
              setSessionStats((prev) => ({ ...prev, queries: prev.queries + 1 }));
            } else if (event.type === 'error') {
              setThinkingSteps([]);
              setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: `❌ Error: ${event.text}` },
              ]);
            }
          } catch {
            // malformed JSON line — skip
          }
        }
      }
    } catch (err) {
      setThinkingSteps([]);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ Error: ${err.message || 'Backend unreachable. Ensure \`python main.py\` is running.'}`,
        },
      ]);
    } finally {
      setLoading(false);
      setThinkingSteps([]);
    }
  };

  return (
    <ResearchContext.Provider
      value={{
        messages, loading, fetchResearch,
        uploadFile, deleteFile, uploadedFiles, setUploadedFiles, refreshFiles,
        selectedHashes, toggleFileSelection,
        thinkingSteps,
        mode, setMode,
        sessionStats,
      }}
    >
      {children}
    </ResearchContext.Provider>
  );
};

export const useResearch = () => {
  const ctx = useContext(ResearchContext);
  if (!ctx) throw new Error('useResearch must be used within a ResearchProvider.');
  return ctx;
};
