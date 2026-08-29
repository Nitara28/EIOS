'use client';

import React, { useEffect, useState } from 'react';
import { CreditCard, AlertTriangle, CheckCircle, Clock, Filter, Send, IndianRupee } from 'lucide-react';
import { fetchApi } from '@/lib/api';

export default function PaymentsPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInvoices();
  }, [statusFilter]);

  async function loadInvoices() {
    try {
      setLoading(true);
      const data = await fetchApi(`/payments/invoices${statusFilter ? `?status=${statusFilter}` : ''}`);
      setInvoices(data);
    } catch (err) {
      console.error('Failed to load invoices:', err);
    } finally {
      setLoading(false);
    }
  }

  const totalOverdue = invoices.reduce((acc, inv) => acc + (inv.days_overdue > 0 ? inv.outstanding_balance : 0), 0);
  const totalOutstanding = invoices.reduce((acc, inv) => acc + inv.outstanding_balance, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Financial Ledger & Invoices</h1>
          <p className="text-sm text-slate-400 mt-1">Track customer billing, overdue aging, receivables, and payment dispatch</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent focus:outline-none text-slate-200"
            >
              <option value="">All Payments</option>
              <option value="OVERDUE">Overdue Only</option>
              <option value="PENDING">Pending</option>
              <option value="PAID">Paid</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary KPI Pills */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase">Total Outstanding</span>
            <h3 className="text-xl font-bold text-white mt-1">₹{totalOutstanding.toLocaleString('en-IN')}</h3>
          </div>
          <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#111827] border border-amber-500/30 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-amber-400 uppercase">Overdue Amount</span>
            <h3 className="text-xl font-bold text-amber-400 mt-1">₹{totalOverdue.toLocaleString('en-IN')}</h3>
          </div>
          <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#111827] border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase">Total Invoices</span>
            <h3 className="text-xl font-bold text-emerald-400 mt-1">{invoices.length}</h3>
          </div>
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400">
            <CreditCard className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Invoice #</th>
                <th className="p-4">Customer</th>
                <th className="p-4">Invoice Amount</th>
                <th className="p-4">Outstanding</th>
                <th className="p-4">Due Date</th>
                <th className="p-4">Status / Aging</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-500">Loading invoices...</td></tr>
              ) : invoices.length === 0 ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-500">No invoices found.</td></tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/40 transition">
                    <td className="p-4 font-mono font-bold text-white">{inv.invoice_number}</td>
                    <td className="p-4">
                      <p className="font-bold text-slate-200">{inv.company_name || inv.customer_name}</p>
                    </td>
                    <td className="p-4 font-semibold text-slate-300">₹{inv.amount.toLocaleString('en-IN')}</td>
                    <td className="p-4 font-bold text-amber-400">
                      ₹{inv.outstanding_balance.toLocaleString('en-IN')}
                    </td>
                    <td className="p-4 text-slate-400">
                      {new Date(inv.due_date).toLocaleDateString()}
                    </td>
                    <td className="p-4">
                      {inv.days_overdue > 0 ? (
                        <span className="px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400 font-bold font-mono">
                          {inv.days_overdue} DAYS OVERDUE
                        </span>
                      ) : inv.status === 'PAID' ? (
                        <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 font-bold">PAID</span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-400 font-bold">PENDING</span>
                      )}
                    </td>
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
