'use client';

import React, { useEffect, useState } from 'react';
import { History, ShieldCheck, ShieldAlert, FileText, Lock } from 'lucide-react';
import { fetchApi } from '@/lib/api';

export default function ActivityLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadLogs() {
      try {
        const data = await fetchApi('/activity-logs');
        setLogs(data);
      } catch (err) {
        console.error('Failed to load activity logs:', err);
      } finally {
        setLoading(false);
      }
    }
    loadLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Immutable System Audit Logs</h1>
          <p className="text-sm text-slate-400 mt-1">Traceable event history of AI decisions, user actions, data imports, and executions</p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg font-mono">
          <Lock className="w-3.5 h-3.5 text-emerald-400" />
          <span>Audit Log Tamper-Proof</span>
        </div>
      </div>

      <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Timestamp</th>
                <th className="p-4">User / Actor</th>
                <th className="p-4">Action</th>
                <th className="p-4">Source System</th>
                <th className="p-4">Risk Rating</th>
                <th className="p-4">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-500">Loading audit history...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-500">No activity logs recorded yet.</td></tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition font-mono">
                    <td className="p-4 text-slate-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="p-4 text-emerald-400 font-bold font-sans">{log.user_name}</td>
                    <td className="p-4 text-white font-sans font-semibold">{log.action}</td>
                    <td className="p-4 text-slate-400">{log.source}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        log.risk_level === 'HIGH' ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-300'
                      }`}>
                        {log.risk_level}
                      </span>
                    </td>
                    <td className="p-4 text-slate-300 font-sans max-w-xs truncate">{log.details}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
