'use client';

import React, { useEffect, useState } from 'react';
import { Briefcase, AlertTriangle, CheckCircle, Clock, Plus, Filter, IndianRupee } from 'lucide-react';
import { fetchApi } from '@/lib/api';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, [statusFilter]);

  async function loadProjects() {
    try {
      setLoading(true);
      const data = await fetchApi(`/projects${statusFilter ? `?status=${statusFilter}` : ''}`);
      setProjects(data);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">COMPLETED</span>;
      case 'IN_PROGRESS':
        return <span className="px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-400 font-bold border border-blue-500/30">IN PROGRESS</span>;
      case 'DELAYED':
        return <span className="px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30 animate-pulse">DELAYED</span>;
      case 'AT_RISK':
        return <span className="px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-400 font-bold border border-amber-500/30">AT RISK</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 font-bold border border-slate-700">PLANNED</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Project Operational Tracking</h1>
          <p className="text-sm text-slate-400 mt-1">Monitor project execution, risk levels, deadlines, and milestone budgets</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent focus:outline-none text-slate-200"
            >
              <option value="">All Statuses</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="DELAYED">Delayed</option>
              <option value="AT_RISK">At Risk</option>
              <option value="COMPLETED">Completed</option>
              <option value="PLANNED">Planned</option>
            </select>
          </div>

          <button className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center space-x-1.5 transition">
            <Plus className="w-4 h-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full p-12 text-center text-slate-500">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="col-span-full p-12 text-center text-slate-500">No projects match the selected filter.</div>
        ) : (
          projects.map((p) => (
            <div key={p.id} className="p-5 rounded-2xl bg-[#111827] border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition">
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <h3 className="font-bold text-base text-white">{p.name}</h3>
                  <div className="text-[10px]">{getStatusBadge(p.status)}</div>
                </div>

                <p className="text-xs text-emerald-400 font-medium mb-3">{p.company_name || p.customer_name}</p>
                <p className="text-xs text-slate-400 line-clamp-2 mb-4">{p.description}</p>

                {/* Progress Bar */}
                <div className="space-y-1 mb-4">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-400">Completion</span>
                    <span className="text-slate-200">{p.progress_percentage}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className={`h-full transition-all ${
                        p.status === 'DELAYED' ? 'bg-rose-500' : p.status === 'AT_RISK' ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${p.progress_percentage}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <div>
                  <span className="text-[10px] uppercase text-slate-500 block">Budget</span>
                  <strong className="text-slate-200">₹{(p.budget || 0).toLocaleString('en-IN')}</strong>
                </div>
                <div className="text-right">
                  <span className="text-[10px] uppercase text-slate-500 block">Due Date</span>
                  <strong className="text-slate-300">{p.due_date ? new Date(p.due_date).toLocaleDateString() : 'N/A'}</strong>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
