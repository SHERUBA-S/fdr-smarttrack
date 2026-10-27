import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FileText, PlusCircle, CheckSquare,
  RefreshCw, Unlock, Building2, ShieldAlert, Database, KeyRound
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const navItems = [
    {
      label: 'Dashboard',
      to: '/',
      icon: LayoutDashboard,
      roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR'] as UserRole[]
    },
    {
      label: 'FDR Records',
      to: '/fdrs',
      icon: FileText,
      roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR'] as UserRole[]
    },
    {
      label: 'New FDR Record',
      to: '/fdrs/create',
      icon: PlusCircle,
      roles: ['SUPER_ADMIN', 'INSTITUTION_USER'] as UserRole[]
    },
    {
      label: 'Review Queue',
      to: '/review-queue',
      icon: CheckSquare,
      roles: ['SUPER_ADMIN', 'REVIEWING_OFFICIAL'] as UserRole[]
    },
    {
      label: 'Renewal Workflow',
      to: '/renewals',
      icon: RefreshCw,
      roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL'] as UserRole[]
    },
    {
      label: 'Release Workflow',
      to: '/releases',
      icon: Unlock,
      roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL'] as UserRole[]
    },
    {
      label: 'Institutions',
      to: '/institutions',
      icon: Building2,
      roles: ['SUPER_ADMIN', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR'] as UserRole[]
    },
    {
      label: 'Audit Trails',
      to: '/audit-logs',
      icon: ShieldAlert,
      roles: ['SUPER_ADMIN', 'READONLY_AUDITOR'] as UserRole[]
    },
    {
      label: 'Dataset Manager',
      to: '/datasets',
      icon: Database,
      roles: ['SUPER_ADMIN'] as UserRole[]
    },
    {
      label: '2FA / MFA Security',
      to: '/mfa-setup',
      icon: KeyRound,
      roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR'] as UserRole[]
    }
  ];

  const allowedItems = navItems.filter(item => user && item.roles.includes(user.role));

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-[calc(100vh-4rem)] border-r border-slate-800">
      <div className="p-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Navigation
      </div>
      <nav className="flex-1 px-3 space-y-1">
        {allowedItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <item.icon className="w-4 h-4 shrink-0" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Security Status Box */}
      <div className="p-4 m-3 rounded-xl bg-slate-800/80 border border-slate-700 text-xs">
        <p className="font-semibold text-slate-200">Security Isolation</p>
        <p className="text-slate-400 mt-1 leading-relaxed">
          {user?.role === 'INSTITUTION_USER'
            ? 'Tenant records strictly isolated to assigned institution.'
            : 'Administrative oversight mode active.'}
        </p>
      </div>
    </aside>
  );
};
