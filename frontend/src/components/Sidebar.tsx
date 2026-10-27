import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FileText, PlusCircle, CheckSquare,
  RefreshCw, Unlock, Building2, ShieldAlert, Database, KeyRound,
  Users, Activity, CheckCircle2, GitBranch, Calendar, Clock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';

interface NavSection {
  title: string;
  items: {
    label: string;
    to: string;
    icon: React.ElementType;
    badge?: string;
    roles: UserRole[];
  }[];
}

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const sections: NavSection[] = [
    {
      title: 'Operations',
      items: [
        {
          label: 'Dashboard',
          to: '/',
          icon: LayoutDashboard,
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        },
        {
          label: 'FDR Records',
          to: '/fdrs',
          icon: FileText,
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        },
        {
          label: 'New FDR Record',
          to: '/fdrs/create',
          icon: PlusCircle,
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER']
        },
        {
          label: 'Review Queue',
          to: '/review-queue',
          icon: CheckSquare,
          roles: ['SUPER_ADMIN', 'REVIEWING_OFFICIAL']
        },
        {
          label: 'Renewal Workflow',
          to: '/renewals',
          icon: RefreshCw,
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL']
        },
        {
          label: 'Release Workflow',
          to: '/releases',
          icon: Unlock,
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL']
        }
      ]
    },
    {
      title: 'Innovations',
      items: [
        {
          label: 'Risk Radar',
          to: '/risk-radar',
          icon: Activity,
          badge: 'Rule Engine',
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        },
        {
          label: 'Consistency Checker',
          to: '/consistency-checker',
          icon: CheckCircle2,
          badge: 'Integrity',
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        },
        {
          label: 'Lifecycle Chain',
          to: '/lifecycle-chain',
          icon: GitBranch,
          badge: 'Traceability',
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        },
        {
          label: 'Maturity Calendar',
          to: '/maturity-calendar',
          icon: Calendar,
          badge: '30/15/7d',
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        },
        {
          label: 'Bottleneck Monitor',
          to: '/bottlenecks',
          icon: Clock,
          badge: 'SLA',
          roles: ['SUPER_ADMIN', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        }
      ]
    },
    {
      title: 'Administration',
      items: [
        {
          label: 'User Management',
          to: '/users',
          icon: Users,
          roles: ['SUPER_ADMIN']
        },
        {
          label: 'Institutions',
          to: '/institutions',
          icon: Building2,
          roles: ['SUPER_ADMIN', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        },
        {
          label: 'Audit Trails',
          to: '/audit-logs',
          icon: ShieldAlert,
          roles: ['SUPER_ADMIN', 'READONLY_AUDITOR']
        },
        {
          label: 'Dataset Manager',
          to: '/datasets',
          icon: Database,
          roles: ['SUPER_ADMIN']
        },
        {
          label: '2FA / MFA Security',
          to: '/mfa-setup',
          icon: KeyRound,
          roles: ['SUPER_ADMIN', 'INSTITUTION_USER', 'REVIEWING_OFFICIAL', 'READONLY_AUDITOR']
        }
      ]
    }
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-[calc(100vh-4rem)] border-r border-slate-800">
      <nav className="flex-1 px-3 py-3 space-y-4 overflow-y-auto">
        {sections.map((section) => {
          const visibleItems = section.items.filter(
            (item) => user && item.roles.includes(user.role)
          );
          if (visibleItems.length === 0) return null;

          return (
            <div key={section.title}>
              <div className="px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {section.title}
              </div>
              <div className="space-y-0.5">
                {visibleItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-xs font-semibold'
                          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <item.icon className="w-4 h-4 shrink-0 text-slate-400 group-hover:text-white" />
                      <span className="truncate">{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-slate-800 text-blue-300 border border-slate-700">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Security Status Box */}
      <div className="p-3 m-3 rounded-xl bg-slate-800/80 border border-slate-700 text-xs shrink-0">
        <p className="font-semibold text-slate-200 text-[11px]">Security Isolation</p>
        <p className="text-slate-400 mt-0.5 leading-relaxed text-[10px]">
          {user?.role === 'INSTITUTION_USER'
            ? 'Tenant records isolated to assigned institution.'
            : 'Administrative oversight mode active.'}
        </p>
      </div>
    </aside>
  );
};
