'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Bot,
  Users,
  Briefcase,
  CreditCard,
  CheckSquare,
  ShieldCheck,
  Database,
  History,
  Settings,
  Search,
  Bell,
  Building2,
  User,
  LogOut,
  Sparkles,
  ChevronDown
} from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<{ full_name?: string; email?: string } | null>(null);
  const [org, setOrg] = useState<{ name?: string } | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('eios_user');
    const orgData = localStorage.getItem('eios_org');
    if (userData) setUser(JSON.parse(userData));
    if (orgData) setOrg(JSON.parse(orgData));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('eios_token');
    localStorage.removeItem('eios_user');
    localStorage.removeItem('eios_org');
    router.push('/login');
  };

  const navItems = [
    { label: 'Dashboard', href: '/', icon: LayoutDashboard },
    { label: 'AI Assistant', href: '/ai-assistant', icon: Bot, badge: 'AI' },
    { label: 'Customers', href: '/customers', icon: Users },
    { label: 'Projects', href: '/projects', icon: Briefcase },
    { label: 'Payments', href: '/payments', icon: CreditCard },
    { label: 'Tasks', href: '/tasks', icon: CheckSquare },
    { label: 'Approvals', href: '/approvals', icon: ShieldCheck, badge: '2' },
    { label: 'Data Sources', href: '/data-sources', icon: Database },
    { label: 'Activity Logs', href: '/activity-logs', icon: History },
    { label: 'Settings', href: '/settings', icon: Settings },
  ];

  if (pathname === '/login' || pathname === '/register') {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen bg-[#0b0f19] text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-[#111827] border-r border-slate-800 flex flex-col flex-shrink-0">
        {/* Brand */}
        <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide flex items-center space-x-1.5">
              <span>EIOS</span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">COO</span>
            </h1>
            <p className="text-[11px] text-slate-400">AI Business Operations</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                    item.badge === 'AI' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom Tagline */}
        <div className="p-4 border-t border-slate-800 bg-[#0d1322]">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Building2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span className="truncate">{org?.name || 'Apex Global Ops'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-[#111827]/80 border-b border-slate-800 backdrop-blur px-6 flex items-center justify-between z-10">
          {/* Global Search */}
          <div className="relative w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search customers, projects, invoices, or ask EIOS..."
              className="w-full bg-slate-900/90 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          {/* Right Header Controls */}
          <div className="flex items-center space-x-4">
            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
              </button>

              {/* Notification Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-[#111827] border border-slate-800 rounded-xl shadow-2xl p-4 z-50">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Notifications</h3>
                    <span className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full font-mono">2 Unread</span>
                  </div>
                  <div className="space-y-3 mt-3">
                    <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800/80 text-xs">
                      <p className="font-medium text-amber-400">Payment Overdue Alert</p>
                      <p className="text-slate-300 mt-0.5">ABC Industries has an invoice of ₹80,000 overdue by 15 days.</p>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800/80 text-xs">
                      <p className="font-medium text-emerald-400">Action Approval Required</p>
                      <p className="text-slate-300 mt-0.5">2 payment reminder dispatches are awaiting manager sign-off.</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Organization Selector */}
            <div className="flex items-center space-x-2 text-xs bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
              <Building2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-medium text-slate-200">{org?.name || 'Apex Global'}</span>
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </div>

            {/* User Profile / Logout */}
            <div className="flex items-center space-x-3 pl-2 border-l border-slate-800">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-emerald-400">
                {user?.full_name?.charAt(0) || 'R'}
              </div>
              <div className="hidden md:block text-left text-xs">
                <p className="font-semibold text-slate-200">{user?.full_name || 'Rajesh Sharma'}</p>
                <p className="text-slate-400 text-[10px]">Owner / Admin</p>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </header>

        {/* Dynamic Page Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0b0f19]">
          {children}
        </main>
      </div>
    </div>
  );
}
