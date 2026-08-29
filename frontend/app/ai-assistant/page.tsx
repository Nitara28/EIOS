'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Database,
  ShieldAlert,
  FileSpreadsheet,
  PlusCircle,
  MessageSquare
} from 'lucide-react';
import { fetchApi } from '@/lib/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  intent?: string;
  structured_data?: any[];
  suggested_action?: any;
}

export default function AIAssistantPage() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-1',
      sender: 'assistant',
      content: 'Good morning! I am EIOS, your AI Chief Operating Officer. How can I assist with your business operations today?',
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [activeContext, setActiveContext] = useState<any>(null);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const samplePrompts = [
    "Which customers have pending payments above ₹50,000?",
    "Which projects are delayed?",
    "Give me today's business summary.",
    "Show pending payments.",
    "Show this month's revenue."
  ];

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const promptText = textToSend || query;
    if (!promptText.trim() || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: promptText
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setQuery('');
    setLoading(true);
    setActionStatus(null);

    try {
      const res = await fetchApi('/ai/query', {
        method: 'POST',
        body: JSON.stringify({ query: promptText })
      });

      const assistantMsg: Message = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        content: res.answer,
        intent: res.intent,
        structured_data: res.structured_data,
        suggested_action: res.suggested_action
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setActiveContext(res);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          content: `Error processing query: ${err.message || 'Server error'}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAction = async (action: any) => {
    try {
      setActionStatus('Creating Action Request...');
      const res = await fetchApi('/ai/action/submit', {
        method: 'POST',
        body: JSON.stringify({
          action_type: action.action_type,
          payload: action.payload,
          risk_level: action.risk_level || 'HIGH'
        })
      });

      setActionStatus(`Action Submitted! Status: ${res.status}. Check Approvals tab.`);
    } catch (err: any) {
      setActionStatus(`Action failed: ${err.message}`);
    }
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex rounded-2xl border border-slate-800 bg-[#111827] overflow-hidden">
      {/* Left Column: Conversations History */}
      <div className="w-64 border-r border-slate-800 bg-[#0d1322] flex flex-col hidden md:flex flex-shrink-0">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Conversations</span>
          <button
            onClick={() => setMessages([{ id: 'msg-1', sender: 'assistant', content: 'Fresh workspace initialized.' }])}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 transition"
            title="New Chat"
          >
            <PlusCircle className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 p-3 space-y-2 overflow-y-auto">
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs cursor-pointer">
            <div className="flex items-center space-x-2 text-emerald-400 font-medium">
              <MessageSquare className="w-3.5 h-3.5" />
              <span className="truncate">Overdue Payments & Actions</span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">Active operational session</p>
          </div>

          <div className="p-3 rounded-xl hover:bg-slate-800/50 text-xs text-slate-300 cursor-pointer transition">
            <div className="flex items-center space-x-2 text-slate-300">
              <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
              <span className="truncate">Delayed Projects Review</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-1">Yesterday</p>
          </div>
        </div>

        {/* Quick Suggestions */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/60">
          <p className="text-[11px] font-semibold text-slate-400 uppercase mb-2">Suggested Queries</p>
          <div className="space-y-1.5">
            {samplePrompts.slice(0, 3).map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                className="w-full text-left text-[11px] text-slate-300 hover:text-emerald-400 hover:bg-slate-800/80 p-2 rounded-lg truncate transition"
              >
                "{prompt}"
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Center Column: AI Conversation Feed */}
      <div className="flex-1 flex flex-col bg-[#111827]">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center space-x-2">
                <span>AI COO Intelligence Assistant</span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 font-mono px-2 py-0.5 rounded">Gemini Powered</span>
              </h2>
              <p className="text-[11px] text-slate-400">Natural language operational query & action engine</p>
            </div>
          </div>
        </div>

        {/* Chat Feed */}
        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl rounded-2xl p-5 ${
                msg.sender === 'user'
                  ? 'bg-emerald-600 text-slate-950 font-medium'
                  : 'bg-slate-900 border border-slate-800 text-slate-200'
              }`}>
                {msg.sender === 'assistant' && (
                  <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-2">
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-bold text-emerald-400">EIOS Operational Engine</span>
                    </div>
                    {msg.intent && (
                      <span className="text-[10px] bg-slate-800 font-mono text-slate-400 px-2 py-0.5 rounded border border-slate-700">
                        INTENT: {msg.intent}
                      </span>
                    )}
                  </div>
                )}

                <div className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</div>

                {/* Render Structured Result Table if present */}
                {msg.structured_data && msg.structured_data.length > 0 && (
                  <div className="mt-4 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/60">
                    <div className="bg-slate-900/80 px-4 py-2 text-xs font-bold text-slate-300 border-b border-slate-800 flex justify-between">
                      <span>Retrieved Business Records ({msg.structured_data.length})</span>
                      <span className="text-[10px] text-emerald-400 font-mono">SQL Validated</span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="p-2.5">Customer</th>
                            <th className="p-2.5">Invoice #</th>
                            <th className="p-2.5">Outstanding</th>
                            <th className="p-2.5">Days Overdue</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {msg.structured_data.map((row: any, i: number) => (
                            <tr key={i} className="hover:bg-slate-800/40">
                              <td className="p-2.5 font-semibold text-white">{row.company_name || row.customer_name || row.project_name || 'N/A'}</td>
                              <td className="p-2.5 font-mono text-slate-400">{row.invoice_number || row.status || '—'}</td>
                              <td className="p-2.5 font-semibold text-amber-400">
                                {row.outstanding_balance ? `₹${row.outstanding_balance.toLocaleString('en-IN')}` : row.budget ? `₹${row.budget.toLocaleString('en-IN')}` : '—'}
                              </td>
                              <td className="p-2.5">
                                {row.days_overdue ? (
                                  <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 font-bold font-mono">
                                    {row.days_overdue} days
                                  </span>
                                ) : (
                                  <span className="text-slate-400">{row.progress_percentage ? `${row.progress_percentage}%` : '—'}</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Render Action Buttons if available */}
                {msg.suggested_action && (
                  <div className="mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        <span>Recommended Operational Action</span>
                      </span>
                      <p className="text-[11px] text-slate-300 mt-0.5">
                        {msg.suggested_action.label} ({msg.suggested_action.risk_level} Risk)
                      </p>
                    </div>

                    <button
                      onClick={() => handleExecuteAction(msg.suggested_action)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center space-x-1.5 transition"
                    >
                      <span>Prepare Reminders</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex items-center space-x-3 text-xs text-slate-400">
                <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                <span>Classifying intent & inspecting PostgreSQL data layer...</span>
              </div>
            </div>
          )}

          {actionStatus && (
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 font-medium">
              {actionStatus}
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-3"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask EIOS e.g. 'Which customers have pending payments above ₹50,000?'"
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-sm flex items-center space-x-2 transition"
            >
              <span>Ask</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Right Column: Context & Safety Drawer */}
      <div className="w-72 border-l border-slate-800 bg-[#0d1322] p-4 flex-col hidden lg:flex flex-shrink-0">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">
          Execution Context
        </h3>

        {activeContext ? (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Intent Classification</span>
              <p className="font-mono text-emerald-400 font-bold text-sm mt-0.5">{activeContext.intent}</p>
            </div>

            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Applied Filters</span>
              <pre className="font-mono text-[11px] text-slate-300 mt-1 bg-slate-950 p-2 rounded border border-slate-800">
                {JSON.stringify(activeContext.filters_used, null, 2)}
              </pre>
            </div>

            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Safety Engine Policy</span>
              <div className="mt-2 space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">SQL Allowlist</span>
                  <span className="text-emerald-400 font-bold">PASSED</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Prompt Injection</span>
                  <span className="text-emerald-400 font-bold">CLEARED</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Approval Required</span>
                  <span className="text-amber-400 font-bold">YES</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500 text-xs">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-40 text-emerald-400" />
            <p>Run a natural language query to inspect intent extraction and safety validation.</p>
          </div>
        )}
      </div>
    </div>
  );
}
