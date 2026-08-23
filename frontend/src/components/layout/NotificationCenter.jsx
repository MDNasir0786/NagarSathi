import React from 'react';
import { X, CheckCheck, Bell } from 'lucide-react';
import { useNotificationStore } from '../../stores/notificationStore';
import { motion, AnimatePresence } from 'framer-motion';

export const NotificationCenter = () => {
  const { isOpen, setOpen, notifications, markAsRead, markAllAsRead } = useNotificationStore();

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="fixed top-16 right-4 z-50 w-80 sm:w-96 bg-white border border-gray-200 rounded-2xl shadow-xl overflow-hidden"
        >
          <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-emerald-50/50">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-emerald-700" />
              <h3 className="font-bold text-gray-900 text-sm">Notifications</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={markAllAsRead}
                className="text-[11px] text-emerald-700 hover:underline flex items-center gap-1 font-semibold"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                Mark all read
              </button>
              <button
                onClick={() => setOpen(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto divide-y divide-gray-100">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-400 text-xs">No notifications yet.</div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  onClick={() => markAsRead(item.id)}
                  className={`p-3.5 hover:bg-gray-50 cursor-pointer transition-colors ${
                    !item.read ? 'bg-emerald-50/20' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-xs font-bold text-gray-900">{item.title}</h4>
                    <span className="text-[10px] text-gray-400 shrink-0">{item.timestamp}</span>
                  </div>
                  <p className="text-xs text-gray-600 mt-0.5">{item.message}</p>
                </div>
              ))
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
