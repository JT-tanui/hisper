import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import * as WebBrowser from 'expo-web-browser';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiClient } from '../../api/client';

interface AuthState {
  token: string | null;
  user?: {
    id: string;
    email: string;
  } | null;
}

interface AuthContextValue extends AuthState {
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const AUTH_TOKEN_KEY = 'hisper-auth-token';
const API_BASE_URL = Constants.expoConfig?.extra?.apiUrl ?? 'https://api.hisper.local';

const AuthProvider = ({ children }: { children: React.ReactNode }): JSX.Element => {
  const [state, setState] = useState<AuthState>({ token: null, user: null });

  React.useEffect(() => {
    AsyncStorage.getItem(AUTH_TOKEN_KEY).then((stored) => {
      if (stored) {
        setState((prev) => ({ ...prev, token: stored }));
      }
    });
  }, []);

  const login = useCallback(async () => {
    const oauthUrl = `${API_BASE_URL}/oauth/authorize`;
    await WebBrowser.openAuthSessionAsync(oauthUrl, 'hisper://callback');
  }, []);

  const logout = useCallback(async () => {
    await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
    setState({ token: null, user: null });
  }, []);

  apiClient.interceptors.request.use((config) => {
    if (state.token) {
      config.headers.Authorization = `Bearer ${state.token}`;
    }
    return config;
  });

  const value = useMemo(() => ({ ...state, login, logout }), [state, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
};

export default AuthProvider;
