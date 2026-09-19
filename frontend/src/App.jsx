import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { 
  FileText, UploadCloud, Send, Database, ShieldCheck, 
  Cpu, CheckCircle2, ChevronRight, Layers, Sparkles 
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);

  const [messages, setMessages] = useState([
    {
      id: "welcome",
      sender: "assistant",
      content: "DocuGauge pipeline initialized. Upload documents to index dense embeddings into pgvector, or query loaded context.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const chatEndRef = useRef(null);

  const fetchDocuments = async () => {
    try {
      const res = await axios.get(`${API_BASE}/documents`);
      setDocuments(res.data || []);
    } catch (err) {
      console.error("Failed to load documents", err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isQuerying]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadMessage({ type: "info", text: "Computing SHA-256 & embedding chunks..." });

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await axios.post(`${API_BASE}/documents/upload`, formData);
      setUploadMessage({ type: "success", text: `Indexed: ${res.data.filename}` });
      setSelectedFile(null);
      await fetchDocuments();
    } catch (err) {
      setUploadMessage({ 
        type: "error", 
        text: err.response?.data?.detail || "Upload or indexing failed." 
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendQuery = async (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || isQuerying) return;

    const userMessage = {
      id: Date.now().toString(),
      sender: "user",
      content: inputQuery,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuery = inputQuery;
    setInputQuery("");
    setIsQuerying(true);

    try {
      const res = await axios.post(`${API_BASE}/rag/query`, {
        query: currentQuery,
        top_k: 3
      });

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        content: res.data.answer,
        citations: res.data.citations || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "assistant",
          content: `Inference Error: ${err.response?.data?.detail || err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        }
      ]);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#0b0f19] text-slate-100 antialiased font-sans">
      {/* Sidebar */}
      <aside className="w-80 border-r border-slate-800 bg-[#0e1424] flex flex-col justify-between">
        <div className="p-5">
          {/* Header */}
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shadow-inner">
              <Cpu size={22} />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                DocuGauge <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono">v1.0</span>
              </h1>
              <p className="text-xs text-slate-400">RAG Engine • pgvector</p>
            </div>
          </div>

          {/* Upload Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <UploadCloud size={14} className="text-indigo-400" /> Ingest Documents
            </h2>
            <form onSubmit={handleUpload} className="space-y-3">
              <label className="block w-full cursor-pointer rounded-lg border border-dashed border-slate-700 bg-slate-800/40 p-3 text-center transition hover:border-slate-600">
                <input
                  type="file"
                  accept=".txt,.pdf"
                  className="hidden"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                />
                <span className="text-xs text-slate-400 truncate block">
                  {selectedFile ? selectedFile.name : "Select .txt or .pdf file"}
                </span>
              </label>

              <button
                type="submit"
                disabled={!selectedFile || isUploading}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition shadow-sm cursor-pointer"
              >
                {isUploading ? "Vectorizing Chunks..." : "Index to pgvector"}
              </button>
            </form>

            {uploadMessage && (
              <p className={`mt-2.5 text-[11px] ${
                uploadMessage.type === "error" ? "text-rose-400" : "text-emerald-400"
              }`}>
                {uploadMessage.text}
              </p>
            )}
          </div>

          {/* Ingested Documents Registry */}
          <div className="mt-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
              <span>Indexed Corpus</span>
              <span className="text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                {documents.length}
              </span>
            </h3>
            <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
              {documents.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-2">No documents indexed yet.</p>
              ) : (
                documents.map((doc) => (
                  <div key={doc.id} className="p-2 rounded-lg bg-slate-900/40 border border-slate-800/80 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 truncate">
                      <FileText size={14} className="text-slate-400 shrink-0" />
                      <span className="truncate text-slate-200">{doc.filename}</span>
                    </div>
                    <span className={`text-[10px] font-mono px-1 rounded ${
                      doc.status === "ready" ? "text-emerald-400 bg-emerald-950/40" : "text-amber-400 bg-amber-950/40"
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Stack Specs Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 text-[11px] text-slate-400 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5"><Database size={13} className="text-sky-400" /> Storage:</span>
            <span className="font-mono text-slate-300">Postgres / pgvector</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5"><Layers size={13} className="text-indigo-400" /> Embeddings:</span>
            <span className="font-mono text-slate-300">nomic-embed-text</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5"><Sparkles size={13} className="text-purple-400" /> Generator:</span>
            <span className="font-mono text-slate-300">Llama 3.2</span>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col bg-[#0b0f19]">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-[#0e1424]/50 backdrop-blur">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>RAG Query Pipeline</span>
            <ChevronRight size={14} />
            <span className="text-slate-200 font-medium">Verified Citation Synthesis</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium bg-emerald-950/40 border border-emerald-800/50 px-2.5 py-1 rounded-full">
              <CheckCircle2 size={12} /> Local Pipeline Active
            </div>
          </div>
        </header>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-2xl rounded-xl p-4 text-sm leading-relaxed shadow-sm ${
                  m.sender === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-900 border border-slate-800 text-slate-200"
                }`}
              >
                <p className="whitespace-pre-wrap">{m.content}</p>

                {m.citations && m.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2">
                    <p className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-1.5">
                      <ShieldCheck size={13} className="text-indigo-400" /> Retrieved pgvector Chunks
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                      {m.citations.map((c, i) => (
                        <div
                          key={i}
                          className="bg-slate-950/60 border border-slate-800 rounded-lg p-2 text-xs flex flex-col justify-between"
                        >
                          <div className="flex items-center justify-between text-slate-400 mb-1">
                            <span className="font-mono text-indigo-300 font-medium">Chunk #{c.chunk_index}</span>
                            <span>{c.page_number ? `p. ${c.page_number}` : "Raw Text"}</span>
                          </div>
                          <div className="flex items-center justify-between mt-1 text-[11px]">
                            <span className="text-slate-400">Cosine Match</span>
                            <span className="font-mono text-emerald-400 font-medium">
                              {(c.score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 px-1">{m.timestamp}</span>
            </div>
          ))}

          {isQuerying && (
            <div className="flex items-center gap-2 text-xs text-indigo-400 font-medium animate-pulse">
              <Sparkles size={14} /> Retrieving nearest vector neighbors and synthesizing response...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-[#0e1424]/40 backdrop-blur">
          <form onSubmit={handleSendQuery} className="max-w-4xl mx-auto flex items-center gap-3">
            <input
              type="text"
              placeholder="Ask a question across your vector database..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700/80 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none transition shadow-inner"
            />
            <button
              type="submit"
              disabled={isQuerying || !inputQuery.trim()}
              className="h-11 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 transition shadow-sm cursor-pointer"
            >
              <Send size={15} /> Send
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
