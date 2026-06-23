import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquare, X, Send, User, Bot, Sparkles, Terminal, Database, 
  ChevronDown, ChevronUp, Copy, Check, AlertCircle, RefreshCw, 
  ChevronLeft, ChevronRight, History, Trash2, Plus
} from 'lucide-react';

// Sub-component for paginated database tables
const DbResultTable = ({ columns, rows }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 5;

  if (!columns || columns.length === 0 || !rows || rows.length === 0) {
    return null;
  }

  const totalPages = Math.ceil(rows.length / rowsPerPage);
  const indexOfLastRow = currentPage * rowsPerPage;
  const indexOfFirstRow = indexOfLastRow - rowsPerPage;
  const currentRows = rows.slice(indexOfFirstRow, indexOfLastRow);

  return (
    <div className="mt-3 w-full border border-slate-200/80 rounded-xl overflow-hidden bg-white shadow-sm font-sans">
      <div className="overflow-x-auto max-w-full">
        <table className="w-full text-xs text-left border-collapse">
          <thead>
            <tr className="bg-slate-100/80 text-slate-600 font-bold border-b border-slate-200">
              {columns.map((col, idx) => (
                <th key={idx} className="px-3 py-2 whitespace-nowrap font-semibold">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {currentRows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-slate-50/50 transition-colors">
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx} className="px-3 py-2 max-w-[200px] truncate whitespace-nowrap">
                    {cell === null || cell === undefined ? (
                      <span className="text-slate-400 italic">null</span>
                    ) : typeof cell === 'boolean' ? (
                      cell ? 'True' : 'False'
                    ) : (() => {
                      const cellStr = String(cell).trim();
                      if (/^-?\d+\.\d+$/.test(cellStr)) {
                        return parseFloat(cellStr).toFixed(2);
                      }
                      if (typeof cell === 'number') {
                        return Number.isInteger(cell) ? cell : cell.toFixed(2);
                      }
                      return cellStr;
                    })()}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="bg-slate-50/80 border-t border-slate-200/80 px-3 py-1.5 flex items-center justify-between text-[11px] text-slate-500 font-medium">
          <span>
            Page {currentPage} of {totalPages} ({rows.length} total)
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="p-1 hover:bg-slate-200/60 disabled:opacity-40 rounded transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="p-1 hover:bg-slate-200/60 disabled:opacity-40 rounded transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Sub-component for Collapsible SQL preview
const SqlViewer = ({ sql }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  if (!sql) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className="mt-2 w-full border border-slate-200/60 rounded-xl overflow-hidden bg-slate-50 shadow-inner">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100/80 transition-colors border-none outline-none"
      >
        <span className="flex items-center gap-1.5 font-outfit">
          <Terminal className="w-3.5 h-3.5 text-brand-500" />
          {isExpanded ? 'Hide SQL Query' : 'View Generated SQL'}
        </span>
        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {isExpanded && (
        <div className="relative border-t border-slate-200/60 p-3 bg-slate-900 text-slate-300 font-mono text-[11px] leading-relaxed break-all overflow-x-auto whitespace-pre-wrap">
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 p-1.5 bg-white/10 hover:bg-white/20 text-white/80 rounded transition-colors border-none outline-none cursor-pointer"
            title="Copy SQL"
          >
            {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <code className="text-emerald-400">{sql}</code>
        </div>
      )}
    </div>
  );
};

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Welcome! 🚀 I am your FleetIQ AI Assistant. I can help you analyze vehicles, drivers, and trips.\n\nAsk me anything, like:\n• *Which driver has the most trips?*\n• *Any critical maintenance alerts?*\n• *Show top 5 vehicles by fuel consumption.*',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);

  const toggleChat = () => setIsOpen(!isOpen);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch('/api/chatbot/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error('Failed to fetch chatbot sessions:', error);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSessions();
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && !showHistory) {
      scrollToBottom();
    }
  }, [messages, isOpen, isLoading, showHistory]);

  const startNewChat = () => {
    setMessages([
      {
        id: 1,
        sender: 'bot',
        text: 'Welcome! 🚀 I am your FleetIQ AI Assistant. I can help you analyze vehicles, drivers, and trips.\n\nAsk me anything, like:\n• *Which driver has the most trips?*\n• *Any critical maintenance alerts?*\n• *Show top 5 vehicles by fuel consumption.*',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setSessionId(null);
    setShowHistory(false);
  };

  const loadSession = async (sId) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/chatbot/sessions/${sId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const msgs = await response.json();
      if (msgs.length === 0) {
        startNewChat();
      } else {
        setMessages(msgs);
        setSessionId(sId);
      }
      setShowHistory(false);
    } catch (error) {
      console.error('Failed to load session messages:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sId, e) => {
    e.stopPropagation();
    try {
      const response = await fetch(`/api/chatbot/sessions/${sId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        fetchSessions();
        if (sessionId === sId) {
          startNewChat();
        }
      }
    } catch (error) {
      console.error('Failed to delete chatbot session:', error);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const queryText = typeof textToSend === 'string' ? textToSend : inputText.trim();
    if (!queryText) return;

    if (typeof textToSend !== 'string') {
      setInputText('');
    }

    const newUserMsg = {
      id: Date.now(),
      sender: 'user',
      text: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: queryText,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        fetchSessions();
      }

      const botResponse = {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.message || 'I successfully queried the database but could not format a natural language response.',
        sql: data.sql,
        columns: data.columns,
        rows: data.rows,
        suggestions: data.suggestions || [],
        status: data.status,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botResponse]);

      // Dispatch log event for the Simulator Console/CMD tab
      window.dispatchEvent(new CustomEvent('chatbot-log', {
        detail: {
          id: Date.now(),
          timestamp: new Date().toLocaleTimeString(),
          query: queryText,
          rewritten: data.rewritten_query || queryText,
          sql: data.sql,
          status: data.status,
          error: data.status === 'error' || data.status === 'db_error' ? data.message : null,
          rowsCount: data.rows ? data.rows.length : 0
        }
      }));
    } catch (error) {
      console.error('Chatbot API error:', error);
      const errorMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: `Error connecting to database helper. ${error.message || ''}\n\nPlease verify that backend server is active and your GROQ_API_KEY is properly configured in the .env file.`,
        status: 'error',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);

      // Dispatch log event for errors
      window.dispatchEvent(new CustomEvent('chatbot-log', {
        detail: {
          id: Date.now(),
          timestamp: new Date().toLocaleTimeString(),
          query: queryText,
          rewritten: queryText,
          sql: null,
          status: 'error',
          error: error.message || 'Error connecting to database helper.',
          rowsCount: 0
        }
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSendMessage();
  };

  // Helper to format simple markdown-like elements such as **bold** and *italics* / bullet points
  const formatMessageText = (text) => {
    if (!text) return '';
    // Format bold: **text** or __text__
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Format italics/bullets: * text or • text
    formatted = formatted.replace(/^\s*[•*]\s*(.*?)$/gm, '<li class="ml-4 list-disc">$1</li>');
    
    // Wrap lists nicely
    if (formatted.includes('<li class="ml-4 list-disc">')) {
      formatted = formatted.replace(/((?:<li class="ml-4 list-disc">.*?<\/li>)+)/gs, '<ul class="my-1.5">$1</ul>');
    }

    // Newlines to breaks (if not inside list tag elements to avoid double spacing)
    formatted = formatted.split('\n').map((line) => {
      if (line.includes('<li') || line.includes('<ul') || line.includes('</ul')) return line;
      return line + '<br />';
    }).join('');

    return <div dangerouslySetInnerHTML={{ __html: formatted }} />;
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={toggleChat}
        className={`fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-2xl transition-all duration-300 transform hover:scale-110 active:scale-95 ${
          isOpen 
            ? 'bg-slate-800 text-white rotate-90 scale-0 opacity-0' 
            : 'bg-brand-500 text-white hover:bg-brand-600 shadow-brand-glow rotate-0 scale-100 opacity-100'
        }`}
        title="Open AI Assistant"
      >
        <MessageSquare className="w-6 h-6" />
      </button>

      {/* Chat Window - Enlarged horizontally & vertically for database content */}
      <div
        className={`fixed bottom-4 right-6 z-50 w-[450px] max-w-[95vw] h-[85vh] max-h-[850px] bg-white rounded-3xl shadow-premium border border-slate-200/60 flex flex-col overflow-hidden transition-all duration-500 transform origin-bottom-right ${
          isOpen ? 'scale-100 opacity-100 translate-y-0' : 'scale-50 opacity-0 translate-y-10 pointer-events-none'
        }`}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-brand-500 to-brand-600 p-4 flex items-center justify-between text-white shrink-0 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
          
          <div className="flex items-center gap-3 relative z-10">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/30 shadow-inner">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-outfit font-extrabold text-lg tracking-tight leading-tight flex items-center gap-1.5">
                FleetIQ SQL Assistant
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              </h3>
              <p className="text-brand-100 text-[10px] font-medium uppercase tracking-wider">Natural Language to SQL Engine</p>
            </div>
          </div>
          
          <div className="flex items-center gap-1.5 relative z-10">
            <button
              onClick={() => {
                setShowHistory(!showHistory);
                if (!showHistory) fetchSessions();
              }}
              className={`p-2 rounded-xl transition-all cursor-pointer border-none outline-none ${
                showHistory ? 'bg-white text-brand-600 font-extrabold shadow-sm' : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
              title="Chat History"
            >
              <History className="w-4 h-4" />
            </button>
            <button
              onClick={toggleChat}
              className="p-2 bg-white/10 hover:bg-white/20 rounded-xl transition-colors backdrop-blur-sm border border-white/10 relative z-10 cursor-pointer border-none outline-none"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Sessions History Screen or Message Area */}
        {showHistory ? (
          <div className="flex-1 overflow-y-auto p-5 bg-slate-50 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Saved Chats</span>
                <button
                  onClick={startNewChat}
                  className="flex items-center gap-1 px-3 py-1.5 bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold font-outfit rounded-xl transition-colors cursor-pointer border-none outline-none shadow-sm"
                >
                  <Plus className="w-3.5 h-3.5" />
                  New Chat
                </button>
              </div>

              {sessions.length === 0 ? (
                <div className="h-60 flex flex-col items-center justify-center text-center p-6 bg-white border border-slate-200/60 rounded-3xl shadow-sm">
                  <div className="p-3 bg-slate-100 text-slate-400 rounded-full mb-3">
                    <MessageSquare className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-bold text-slate-700">No saved chats yet</p>
                  <p className="text-xs text-slate-400 mt-1">Start typing a new message to create a session.</p>
                </div>
              ) : (
                <div className="space-y-2.5 max-h-[55vh] overflow-y-auto pr-1">
                  {sessions.map((session) => {
                    const isActive = session.session_id === sessionId;
                    return (
                      <div
                        key={session.session_id}
                        onClick={() => loadSession(session.session_id)}
                        className={`group w-full p-3.5 rounded-2xl border transition-all flex items-center justify-between cursor-pointer ${
                          isActive
                            ? 'bg-brand-50/70 border-brand-200 text-brand-700 shadow-sm font-extrabold'
                            : 'bg-white hover:bg-slate-50/80 border-slate-200/60 text-slate-700 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex-1 min-w-0 pr-2">
                          <p className="text-xs font-bold truncate leading-snug">{session.title}</p>
                          <span className="text-[9px] text-slate-400 font-bold block mt-1">
                            {new Date(session.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })} at{' '}
                            {new Date(session.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <button
                          onClick={(e) => deleteSession(session.session_id, e)}
                          className="p-1.5 bg-transparent hover:bg-rose-50 text-slate-400 hover:text-rose-500 rounded-xl transition-all cursor-pointer opacity-80 hover:opacity-100 border-none outline-none active:scale-95"
                          title="Delete Chat"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <button
              onClick={() => setShowHistory(false)}
              className="w-full py-2.5 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-700 text-xs font-bold font-outfit rounded-xl transition-colors cursor-pointer outline-none mt-4 shrink-0 shadow-sm"
            >
              Back to Chat
            </button>
          </div>
        ) : (
          /* Normal Message Area & Input */
          <>
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-5 bg-slate-50/50 space-y-4">
              {messages.map((msg) => {
                const isBot = msg.sender === 'bot';
                const isError = msg.status === 'error' || msg.status === 'db_error' || msg.status === 'blocked';
                const isOutScope = msg.status === 'out_of_scope' || msg.status === 'cannot_generate';
                
                return (
                  <div key={msg.id} className={`flex items-start gap-2.5 ${isBot ? 'flex-row' : 'flex-row-reverse'}`}>
                    {/* Avatar */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
                      isBot 
                        ? isError 
                          ? 'bg-rose-100 text-rose-600 border border-rose-200' 
                          : 'bg-brand-100 text-brand-600 border border-brand-200' 
                        : 'bg-slate-200 text-slate-600'
                    }`}>
                      {isBot ? (
                        isError ? <AlertCircle className="w-4 h-4" /> : <Bot className="w-4 h-4" />
                      ) : (
                        <User className="w-4 h-4" />
                      )}
                    </div>

                    {/* Message Bubble */}
                    <div className={`max-w-[85%] flex flex-col ${isBot ? 'items-start' : 'items-end'} w-full`}>
                      <div
                        className={`px-4 py-3 rounded-2xl text-[13px] font-medium leading-relaxed shadow-sm w-full ${
                          isBot
                            ? isError
                              ? 'bg-rose-50/70 text-rose-800 border border-rose-200/60 rounded-bl-sm'
                              : isOutScope
                                ? 'bg-amber-50/60 text-slate-700 border border-amber-200/60 rounded-bl-sm'
                                : 'bg-white text-slate-700 border border-slate-200/60 rounded-bl-sm'
                            : 'bg-brand-500 text-white rounded-br-sm max-w-[fit-content]'
                        }`}
                      >
                        {isBot ? formatMessageText(msg.text) : msg.text}

                        {/* Data Table (if rows exist) */}
                        {isBot && msg.columns && msg.rows && msg.rows.length > 0 && (
                          <DbResultTable columns={msg.columns} rows={msg.rows} />
                        )}

                        {/* Suggestion Chips */}
                        {isBot && msg.suggestions && msg.suggestions.length > 0 && (
                          <div className="mt-3.5 border-t border-slate-100 pt-3 flex flex-col gap-2">
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                              <Database className="w-3.5 h-3.5 text-brand-500" />
                              Suggested Queries
                            </span>
                            <div className="flex flex-col gap-1.5">
                              {msg.suggestions.map((sug, idx) => {
                                const sugClean = sug.replace(/\*/g, "");
                                return (
                                  <button
                                    key={idx}
                                    onClick={() => handleSendMessage(sugClean)}
                                    className="text-left w-full px-3 py-2 text-xs font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100/70 border border-brand-100 rounded-xl transition-all cursor-pointer outline-none"
                                  >
                                    💡 {sugClean}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                      <span className="text-[9px] text-slate-400 font-bold mt-1 px-1">
                        {msg.timestamp}
                      </span>
                    </div>
                  </div>
                );
              })}

              {/* Typing Indicator */}
              {isLoading && (
                <div className="flex items-start gap-2.5 flex-row">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm bg-brand-100 text-brand-600 border border-brand-200">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="max-w-[85%] flex flex-col items-start">
                    <div className="px-4 py-3 rounded-2xl bg-white border border-slate-200/60 rounded-bl-sm flex items-center justify-center gap-1 w-16 h-9">
                      <div className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-slate-100 shrink-0">
              <form onSubmit={handleFormSubmit} className="relative flex items-end gap-2">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleFormSubmit(e);
                    }
                  }}
                  placeholder="Ask questions (e.g. 'Show top 5 drivers by trip count', 'Brake wear rating for vehicle id x')..."
                  rows={2}
                  className="flex-1 bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl pl-4 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all placeholder-slate-400 font-medium resize-none leading-relaxed"
                />
                <button
                  type="submit"
                  disabled={isLoading || !inputText.trim()}
                  className="p-3 bg-brand-500 hover:bg-brand-600 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl transition-colors shadow-sm shrink-0 border-none outline-none cursor-pointer"
                >
                  {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </form>
              <div className="text-center mt-2">
                <span className="text-[9px] text-slate-400 font-medium">Press Enter to send · Shift+Enter for newline</span>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default Chatbot;
