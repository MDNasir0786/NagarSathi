import { create } from 'zustand';
import { MOCK_USERS } from '../services/mockData';
import { authService } from '../services';

const getInitialRole = () => {
  try {
    const saved = localStorage.getItem('smart_bhopal_active_role');
    return saved || 'CITIZEN';
  } catch {
    return 'CITIZEN';
  }
};

const initialRole = getInitialRole();

export const useAuthStore = create((set) => ({
  user: MOCK_USERS[initialRole],
  role: initialRole,
  isAuthenticated: true,
  isLoading: false,

  setRole: async (role) => {
    set({ isLoading: true });
    try {
      localStorage.setItem('smart_bhopal_active_role', role);
      const user = await authService.getCurrentUser(role);
      set({ role, user, isAuthenticated: true, isLoading: false });
    } catch (e) {
      console.error('Failed to change role', e);
      set({ isLoading: false });
    }
  },

  login: async (email, role) => {
    set({ isLoading: true });
    try {
      localStorage.setItem('smart_bhopal_active_role', role);
      const user = await authService.login(email, role);
      set({ role, user, isAuthenticated: true, isLoading: false });
    } catch (e) {
      console.error('Login error', e);
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('smart_bhopal_active_role');
    set({ user: null, isAuthenticated: false, role: 'CITIZEN' });
  },
}));
