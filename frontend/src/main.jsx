// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';
// Ensure this path is correct
import { ResearchProvider } from './context/ResearchContext'; 

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ResearchProvider>
      <App />
    </ResearchProvider>
  </React.StrictMode>,
);