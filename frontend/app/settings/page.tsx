'use client';

import React, { useEffect, useState } from 'react';
import { Settings, Building2, Users, Bot, Key, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { fetchApi } from '@/lib/api';

export default function SettingsPage() {
  const [settingsData, setSettingsData] = useState<any>(null);
  const [geminiKey, setGeminiKey] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await fetchApi('/settings');
        setSettingsData(data);
      } catch (err) {
        console.error('Failed to load settings:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-wide">Platform Configuration & Settings</h1>
        <p className="text-sm text-slate-400 mt-1">Manage organization details, team RBAC roles, and AI model parameters</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Organization Card */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-emerald-400">
            <Building2 className="w-5 h-5" />
            <h3 className="font-bold text-base text-white">Organization Profile</h3>
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-500 uppercase font-semibold text-[10px]">Company Name</label>
              <p className="text-white font-medium text-sm mt-0.5">{settingsData?.organization?.name || 'Apex Global Operations'}</p>
            </div>
            <div>
              <label className="text-slate-500 uppercase font-semibold text-[10px]">Industry</label>
              <p className="text-slate-300 mt-0.5">{settingsData?.organization?.industry || 'Industrial Manufacturing'}</p>
            </div>
            <div>
              <label className="text-slate-500 uppercase font-semibold text-[10px]">Currency</label>
              <p className="text-slate-300 font-mono mt-0.5">{settingsData?.organization?.currency || 'INR (₹)'}</p>
            </div>
          </div>
        </div>

        {/* AI Model Configuration Card */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-emerald-400">
            <Bot className="w-5 h-5" />
            <h3 className="font-bold text-base text-white">AI Engine Configuration</h3>
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-500 uppercase font-semibold text-[10px]">AI Provider</label>
              <p className="text-emerald-400 font-bold mt-0.5">Google Gemini 1.5 Flash</p>
            </div>

            <div>
              <label className="text-slate-500 uppercase font-semibold text-[10px]">GEMINI_API_KEY</label>
              <input
                type="password"
                placeholder="Environment Variable Configured"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-slate-200 mt-1 text-xs focus:outline-none focus:border-emerald-500/50"
              />
            </div>

            <div className="pt-2 flex items-center justify-between">
              <span className="text-slate-400">Prompt Injection Defense:</span>
              <span className="text-emerald-400 font-bold">ACTIVE</span>
            </div>
          </div>
        </div>

        {/* Team Members & RBAC Card */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-emerald-400">
            <Users className="w-5 h-5" />
            <h3 className="font-bold text-base text-white">Team & RBAC</h3>
          </div>
          <div className="space-y-2 text-xs">
            {settingsData?.team?.map((member: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800">
                <div>
                  <p className="font-semibold text-slate-200">{member.name}</p>
                  <p className="text-[10px] text-slate-500">{member.email}</p>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono font-bold text-[10px]">
                  {member.role}
                </span>
              </div>
            )) || (
              <div className="p-2 rounded bg-slate-900 text-slate-400">
                Rajesh Sharma (OWNER)
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
