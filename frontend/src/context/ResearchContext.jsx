import { createContext, useContext, useState } from 'react';
import axios from 'axios';

// 1. Create the context
const ResearchContext = createContext(null);

const API_BASE = 'http://localhost:8000/api';

// 2. Create the Provider
export const ResearchProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('research');
  const [uploadedFiles, setUploadedFiles] = useState([]); // { name, chunks, status }

  const uploadFile = async (file) => {
    // Add a pending entry immediately so the UI can show progress
    const entry = { name: file.name, chunks: null, status: 'uploading' };
    setUploadedFiles((prev) => [...prev, entry]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { message, chunks_indexed } = response.data;

      // Mark as done
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.name === file.name ? { ...f, chunks: chunks_indexed, status: 'done' } : f
        )
      );

      // Show a system message in the chat
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `📄 **File uploaded:** \`${file.name}\` — ${chunks_indexed} chunks indexed into the knowledge base. You can now ask questions about it.`,
        },
      ]);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Unknown error';
      setUploadedFiles((prev) =>
        prev.map((f) => (f.name === file.name ? { ...f, status: 'error' } : f))
      );
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ **Upload failed for \`${file.name}\`:** ${detail}`,
        },
      ]);
    }
  };

  const fetchResearch = async (topic) => {
    // Add user message to UI immediately
    const userMsg = { role: 'user', content: topic };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/research`, { topic });
      const aiMsg = { role: 'assistant', content: response.data.report };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Backend unreachable. Ensure `python main.py` is running on port 8000.';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${detail}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const value = { 
    messages, 
    loading, 
    fetchResearch,
    uploadFile,
    uploadedFiles,
    mode, 
    setMode 
  };

  return (
    <ResearchContext.Provider value={value}>
      {children}
    </ResearchContext.Provider>
  );
};

// 3. Create the hook with safety checks
export const useResearch = () => {
  const context = useContext(ResearchContext);
  
  // This check prevents the "Cannot destructure... as it is undefined" error
  if (!context) {
    throw new Error("useResearch must be used within a ResearchProvider. Check your main.jsx wrapper.");
  }
  
  return context;
};