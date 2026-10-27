import React, { useState, useEffect } from 'react';
import { X, Bell, CheckCircle2, Clock, AlertTriangle, ExternalLink } from 'lucide-react';
import { NotificationItem } from '../types';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onRefreshNeeded?: () => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  onRefreshNeeded
}) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchNotifs = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications();
      setNotifications(data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchNotifs();
    }
  }, [isOpen]);

  const markAllRead = async () => {
    await api.markAllNotificationsRead();
    fetchNotifs();
    if (onRefreshNeeded) onRefreshNeeded();
  };

  const markOneRead = async (id: string) => {
    await api.markNotificationRead(id);
    fetchNotifs();
    if (onRefreshNeeded) onRefreshNeeded();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs" onClick={onClose} />
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-blue-600" />
              <h2 className="text-base font-semibold text-slate-800">Notifications Center</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={markAllRead}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1 rounded-sm hover:bg-blue-50"
              >
                Mark all read
              </button>
              <button
                onClick={onClose}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {loading ? (
              <div className="text-center py-8 text-sm text-slate-400">Loading alerts...</div>
            ) : notifications.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
                <p className="text-sm font-medium text-slate-700">All caught up!</p>
                <p className="text-xs text-slate-400 mt-1">No pending regulatory or maturity alerts.</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3.5 rounded-lg border text-sm transition-all ${
                    n.is_read
                      ? 'bg-white border-slate-200 text-slate-600'
                      : 'bg-blue-50/50 border-blue-200/80 text-slate-900 font-medium'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {n.category.includes('OVERDUE') ? (
                        <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
                      ) : (
                        <Clock className="w-4 h-4 text-amber-500 shrink-0" />
                      )}
                      <span className="font-semibold text-xs text-slate-800">{n.title}</span>
                    </div>
                    {!n.is_read && (
                      <button
                        onClick={() => markOneRead(n.id)}
                        className="text-[10px] text-blue-600 hover:underline shrink-0"
                      >
                        Read
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">{n.message}</p>
                  <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100">
                    <span>{new Date(n.created_at).toLocaleDateString()}</span>
                    {n.link && (
                      <Link
                        to={n.link}
                        onClick={onClose}
                        className="flex items-center gap-1 text-blue-600 hover:underline font-medium"
                      >
                        View Record <ExternalLink className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
