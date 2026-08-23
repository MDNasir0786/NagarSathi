import { create } from 'zustand';
import { INITIAL_NOTIFICATIONS } from '../services/mockData';

export const useNotificationStore = create((set) => ({
  isOpen: false,
  notifications: INITIAL_NOTIFICATIONS,
  setOpen: (open) => set({ isOpen: open }),
  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  markAsRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    })),
  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
    })),
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        { ...notification, id: `notif-${Date.now()}`, timestamp: 'Just now', read: false },
        ...state.notifications,
      ],
    })),
}));
