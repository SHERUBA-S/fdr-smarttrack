import React, { useState, useEffect } from 'react';
import { Bell, ShieldCheck, User as UserIcon, LogOut, KeyRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { NotificationDrawer } from './NotificationDrawer';
import { Link } from 'react-router-dom';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const fetchUnread = async () => {
    try {
      const data = await api.getNotifications();
      setUnreadCount(data.unread_count);
    } catch {
      // silently ignore if unauthenticated
    }
  };

  useEffect(() => {
    if (user) {
      fetchUnread();
      const interval = setInterval(fetchUnread, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  return (
    <>
      <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-30 px-6 flex items-center justify-between">
        {/* Left: Branding & Disclaimer */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-700 flex items-center justify-center text-white shadow-xs">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-slate-900 tracking-tight text-base">FDR SmartTrack</span>
              <span className="text-[10px] text-blue-600 bg-blue-50 font-semibold px-2 py-0.5 rounded-full ml-2 border border-blue-200">
                SIH26265
              </span>
            </div>
          </div>
          <span className="hidden lg:inline-block text-[11px] text-slate-500 bg-slate-50 px-3 py-1 rounded-md border border-slate-200/80">
            Administrative Prototype &bull; External Bank Verification Pending
          </span>
        </div>

        {/* Right: User Menu & Notification */}
        <div className="flex items-center gap-3">
          {/* Notifications Trigger */}
          <button
            onClick={() => setIsDrawerOpen(true)}
            className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* User Details */}
          {user && (
            <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-semibold text-slate-900">{user.full_name}</p>
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  {user.role}
                </span>
              </div>

              {/* MFA Setup link */}
              <Link
                to="/mfa-setup"
                className="p-2 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors"
                title="MFA Security Settings"
              >
                <KeyRound className="w-4 h-4" />
              </Link>

              {/* Logout Button */}
              <button
                onClick={logout}
                className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </header>

      <NotificationDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onRefreshNeeded={fetchUnread}
      />
    </>
  );
};
