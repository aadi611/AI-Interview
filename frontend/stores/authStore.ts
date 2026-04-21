import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";

interface User {
  id: string;
  name: string;
  email: string;
  is_admin?: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const res = await api.auth.login(email, password);
          localStorage.setItem("access_token", res.access_token);
          set({ user: res.user, token: res.access_token });
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (name, email, password) => {
        set({ isLoading: true });
        try {
          const res = await api.auth.register({ name, email, password });
          localStorage.setItem("access_token", res.access_token);
          set({ user: res.user, token: res.access_token });
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        set({ user: null, token: null });
      },

      hydrate: async () => {
        const token = localStorage.getItem("access_token");
        if (!token) return;
        try {
          const user = await api.auth.me();
          set({ user, token });
        } catch {
          localStorage.removeItem("access_token");
          set({ user: null, token: null });
        }
      },
    }),
    { name: "auth-store", partialize: (s) => ({ user: s.user, token: s.token }) }
  )
);
