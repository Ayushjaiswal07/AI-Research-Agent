import { createContext, useContext, useState } from 'react';
import axios from 'axios';

// 1. Create the context
const ResearchContext = createContext(null);

// 2. Create the Provider
export const ResearchProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('research');

  const fetchResearch = async (topic) => {
    // Debugging trace
    console.log("DEBUG: fetchResearch triggered for topic:", topic);
    
    // Add user message to UI immediately
    const userMsg = { role: 'user', content: topic };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      console.log("DEBUG: Attempting to call http://localhost:8000/api/research");
      
      // Axios request to your FastAPI backend
      const response = await axios.post('http://localhost:8000/api/research', { 
        topic: topic 
      });
      
      console.log("DEBUG: Backend response data:", response.data);
      
      // Add AI response to UI
      const aiMsg = { role: 'assistant', content: response.data.report };
      setMessages((prev) => [...prev, aiMsg]);
      
    } catch (err) {
      console.error("DEBUG: Backend Request Failed. Details:", err);
      
      // Fallback UI error message
      setMessages((prev) => [
        ...prev, 
        { 
          role: 'assistant', 
          content: 'Error: Backend unreachable. Ensure `python main.py` is running on port 8000 and CORS is enabled.' 
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const value = { 
    messages, 
    loading, 
    fetchResearch, 
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