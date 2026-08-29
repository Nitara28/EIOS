'use client';

import React, { useEffect, useState } from 'react';
import { Users, Search, Plus, Building2, Mail, Phone, IndianRupee, FileText, ChevronRight, X, Briefcase, CreditCard, Clock, Sparkles } from 'lucide-react';
import { fetchApi } from '@/lib/api';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [customerDetails, setCustomerDetails] = useState<any>(null);

  useEffect(() => {
    loadCustomers();
  }, [search]);

  async function loadCustomers() {
    try {
      setLoading(true);
      const data = await fetchApi(`/customers${search ? `?search=${encodeURIComponent(search)}` : ''}`);
      setCustomers(data);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setLoading(false);
    }
  }

  const handleOpenProfile = async (customer: any) => {
    setSelectedCustomer(customer);
    try {
      const data = await fetchApi(`/customers/${customer.id}`);
      setCustomerDetails(data);
    } catch (err) {
      console.error('Failed to load customer profile:', err);
    }
  };

  return (
    <div className="space-y-6 relative">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Customer Operations Directory</h1>
          <p className="text-sm text-slate-400 mt-1">Manage accounts, financial balances, active projects, and contact points</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="relative w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search customers or GSTIN..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          <button className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center space-x-1.5 transition">
            <Plus className="w-4 h-4" />
            <span>Add Customer</span>
          </button>
        </div>
      </div>

      {/* Customers Table Container */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Customer / Organization</th>
                <th className="p-4">Contact Info</th>
                <th className="p-4">GSTIN</th>
                <th className="p-4">Active Projects</th>
                <th className="p-4">Outstanding Receivables</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">Loading customers...</td>
                </tr>
              ) : customers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">No customers found. Upload data via Data Sources.</td>
                </tr>
              ) : (
                customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition">
                    <td className="p-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-emerald-400">
                          {c.name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-white text-sm">{c.name}</p>
                          <p className="text-slate-400 text-[11px]">{c.company_name}</p>
                        </div>
                      </div>
                    </td>

                    <td className="p-4 space-y-1">
                      {c.email && (
                        <div className="flex items-center space-x-1.5 text-slate-300">
                          <Mail className="w-3 h-3 text-slate-500" />
                          <span>{c.email}</span>
                        </div>
                      )}
                      {c.phone && (
                        <div className="flex items-center space-x-1.5 text-slate-400">
                          <Phone className="w-3 h-3 text-slate-500" />
                          <span>{c.phone}</span>
                        </div>
                      )}
                    </td>

                    <td className="p-4 font-mono text-slate-400">{c.gstin || '—'}</td>

                    <td className="p-4">
                      <span className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 font-semibold border border-slate-700">
                        {c.projects_count} Projects
                      </span>
                    </td>

                    <td className="p-4 font-bold text-sm">
                      {c.outstanding_balance > 0 ? (
                        <span className="text-amber-400">₹{c.outstanding_balance.toLocaleString('en-IN')}</span>
                      ) : (
                        <span className="text-emerald-400">Clear</span>
                      )}
                    </td>

                    <td className="p-4 text-right">
                      <button
                        onClick={() => handleOpenProfile(c)}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 inline-flex items-center space-x-1 transition"
                      >
                        <span>View Profile</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Customer Profile Slide-over Drawer */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-[#111827] border-l border-slate-800 h-full p-6 overflow-y-auto space-y-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-lg">
                    {selectedCustomer.name.charAt(0)}
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white">{selectedCustomer.name}</h2>
                    <p className="text-xs text-slate-400">{selectedCustomer.company_name}</p>
                  </div>
                </div>
                <button
                  onClick={() => { setSelectedCustomer(null); setCustomerDetails(null); }}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Profile Details */}
              <div className="mt-6 space-y-6">
                {/* Contact Pill */}
                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                  <div>
                    <span className="text-slate-500 text-[10px] uppercase font-bold">Email</span>
                    <p className="text-slate-200 font-mono mt-0.5">{selectedCustomer.email || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] uppercase font-bold">Phone</span>
                    <p className="text-slate-200 font-mono mt-0.5">{selectedCustomer.phone || 'N/A'}</p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-500 text-[10px] uppercase font-bold">GSTIN</span>
                    <p className="text-emerald-400 font-mono mt-0.5">{selectedCustomer.gstin || 'Unspecified'}</p>
                  </div>
                </div>

                {/* Invoices List */}
                <div>
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                    <CreditCard className="w-3.5 h-3.5 text-amber-400" />
                    <span>Invoices & Billing</span>
                  </h3>
                  <div className="space-y-2">
                    {customerDetails?.invoices?.length > 0 ? (
                      customerDetails.invoices.map((inv: any) => (
                        <div key={inv.id} className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex justify-between items-center text-xs">
                          <div>
                            <p className="font-mono font-bold text-white">{inv.invoice_number}</p>
                            <p className="text-[10px] text-slate-400">Due: {new Date(inv.due_date).toLocaleDateString()}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-amber-400">₹{(inv.amount - inv.paid_amount).toLocaleString('en-IN')}</p>
                            <span className="text-[10px] font-mono uppercase text-slate-500">{inv.status}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500">No active invoices recorded.</p>
                    )}
                  </div>
                </div>

                {/* Projects List */}
                <div>
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Active Projects</span>
                  </h3>
                  <div className="space-y-2">
                    {customerDetails?.projects?.length > 0 ? (
                      customerDetails.projects.map((p: any) => (
                        <div key={p.id} className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex justify-between items-center text-xs">
                          <div>
                            <p className="font-bold text-white">{p.name}</p>
                            <p className="text-[10px] text-slate-400">Progress: {p.progress_percentage}%</p>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[10px]">
                            {p.status}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500">No active projects assigned.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => { setSelectedCustomer(null); setCustomerDetails(null); }}
                className="px-4 py-2 rounded-lg bg-slate-800 text-slate-200 text-xs font-semibold hover:bg-slate-700"
              >
                Close Profile
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
