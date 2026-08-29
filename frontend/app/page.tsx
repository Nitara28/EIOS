'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  IndianRupee,
  Clock,
  AlertTriangle,
  Briefcase,
  CheckSquare,
  ShieldCheck,
  Sparkles,
  ArrowUpRight,
  TrendingUp,
  Upload,
  MessageSquare,
  BellRing
} from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const res = await fetchApi('/dashboard/summary');
        setData(res);
      } catch (err) {
        console.error('Failed to load dashboard summary:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Analyzing business data stream...</p>
        </div>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const aiSummary = data?.ai_summary || {};
  const revenueChart = data?.revenue_chart || [];
  const projectDist = data?.project_distribution || [];

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#64748b'];

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Operational Intelligence Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time status across customers, payments, projects, and automated actions</p>
        </div>

        {/* Quick Actions Bar */}
        <div className="flex items-center space-x-3">
          <Link
            href="/ai-assistant"
            className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs flex items-center space-x-2 transition"
          >
            <Sparkles className="w-4 h-4" />
            <span>Ask EIOS</span>
          </Link>

          <Link
            href="/data-sources"
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-2 transition"
          >
            <Upload className="w-4 h-4 text-emerald-400" />
            <span>Upload Data</span>
          </Link>

          <Link
            href="/approvals"
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-2 transition"
          >
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>Review Approvals</span>
          </Link>
        </div>
      </div>

      {/* AI Business Briefing Card */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 relative overflow-hidden">
        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 flex-shrink-0">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">EIOS Daily Operational Briefing</span>
              <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400">Updated just now</span>
            </div>
            <p className="text-sm font-medium text-slate-100 mt-1">
              {aiSummary?.summary_text || "Good morning. EIOS found 3 delayed projects, ₹2.4L in overdue payments, and 7 follow-ups requiring attention."}
            </p>
            {aiSummary?.priority_recommendation && (
              <div className="mt-3 p-3 rounded-lg bg-slate-950/60 border border-emerald-500/20 flex items-center justify-between text-xs">
                <span className="text-slate-300">
                  <strong className="text-emerald-400">Priority Recommendation:</strong> {aiSummary.priority_recommendation}
                </span>
                <Link href="/ai-assistant" className="text-emerald-400 hover:underline flex items-center space-x-1 font-semibold flex-shrink-0 ml-4">
                  <span>Take Action</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Collected Revenue */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Collected Revenue</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <IndianRupee className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-white">₹{(kpis.total_revenue || 0).toLocaleString('en-IN')}</h3>
            <p className="text-xs text-emerald-400 mt-1 flex items-center space-x-1">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>+18.4% this quarter</span>
            </p>
          </div>
        </div>

        {/* Metric 2: Pending Payments */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Pending Payments</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-white">₹{(kpis.pending_payments || 0).toLocaleString('en-IN')}</h3>
            <p className="text-xs text-slate-400 mt-1">Outstanding receivables</p>
          </div>
        </div>

        {/* Metric 3: Overdue Payments */}
        <div className="p-5 rounded-xl bg-[#111827] border border-amber-500/30 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-amber-400">Overdue Payments</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-amber-400">₹{(kpis.overdue_payments || 0).toLocaleString('en-IN')}</h3>
            <p className="text-xs text-amber-300/80 mt-1 font-mono">Action required: Prepare reminders</p>
          </div>
        </div>

        {/* Metric 4: Delayed Projects */}
        <div className="p-5 rounded-xl bg-[#111827] border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Delayed Projects</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-2xl font-bold text-white">{kpis.delayed_projects || 0} <span className="text-sm font-normal text-slate-400">/ {kpis.active_projects || 0} active</span></h3>
            <p className="text-xs text-rose-400 mt-1">Requiring schedule adjustment</p>
          </div>
        </div>
      </div>

      {/* Analytics & Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Trend Chart */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-[#111827] border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Revenue & Overdue Trend</h3>
              <p className="text-xs text-slate-400">Monthly collection vs overdue aging</p>
            </div>
            <span className="text-xs text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded">FY 2026</span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueChart}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff' }}
                  formatter={(value: any) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Amount']}
                />
                <Area type="monotone" dataKey="revenue" stroke="#10b981" fillOpacity={1} fill="url(#colorRev)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Project Health Distribution */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white mb-1">Project Portfolio Health</h3>
            <p className="text-xs text-slate-400 mb-4">Distribution by current project status</p>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={projectDist} layout="vertical">
                  <XAxis type="number" stroke="#64748b" fontSize={12} />
                  <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} width={90} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {projectDist.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Pending Approvals: <strong className="text-amber-400">{kpis.pending_approvals || 0}</strong></span>
            <Link href="/projects" className="text-emerald-400 hover:underline">View All Projects →</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
