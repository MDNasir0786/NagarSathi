import { create } from 'zustand';
import { MOCK_USERS } from '../services/mockData';
import { authService } from '../services';
import { USE_MOCK } from '../services/apiClient';

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
  user: USE_MOCK ? MOCK_USERS[initialRole] : null,
  role: initialRole,
  isAuthenticated: USE_MOCK,
  isLoading: !USE_MOCK,

  initialize: async () => {
    if (USE_MOCK) return;
    try {
      const user = await authService.getCurrentUser();
      const role = user.role || 'CITIZEN';
      localStorage.setItem('smart_bhopal_active_role', role);
      set({ user, role, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  loginWithOAuth: async (provider) => {
    set({ isLoading: true });
    try {
      await authService.signInWithOAuth(provider);
    } catch (error) {
      console.error('OAuth login error', error);
      set({ isLoading: false });
      throw error;
    }
  },

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
    authService.signOut();
    localStorage.removeItem('smart_bhopal_active_role');
    set({ user: null, isAuthenticated: false, role: 'CITIZEN' });
  },
}));
