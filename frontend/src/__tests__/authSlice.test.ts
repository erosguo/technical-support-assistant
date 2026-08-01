import { describe, it, expect, beforeEach } from 'vitest';
import reducer, {
  logout,
  clearError,
  setUser,
  AuthState,
} from '../store/authSlice';

const initialState: AuthState = {
  token: null,
  user: null,
  loading: false,
  error: null,
};

describe('authSlice', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return initial state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.user).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should handle logout', () => {
    localStorage.setItem('tech_support_token', 'some-token');
    const loggedIn: AuthState = {
      token: 'some-token',
      user: { id: '1', email: 'a@b.c', name: 'A', role: 'admin', is_active: true },
      loading: false,
      error: null,
    };
    const state = reducer(loggedIn, logout());
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(localStorage.getItem('tech_support_token')).toBeNull();
  });

  it('should handle clearError', () => {
    const state: AuthState = { ...initialState, error: 'some error' };
    const cleared = reducer(state, clearError());
    expect(cleared.error).toBeNull();
  });

  it('should handle setUser', () => {
    const user = { id: '1', email: 'a@b.c', name: 'A', role: 'admin', is_active: true };
    const state = reducer(initialState, setUser(user));
    expect(state.user).toEqual(user);
  });

  it('should handle login.pending', () => {
    const state = reducer(initialState, { type: 'auth/login/pending' });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('should handle login.fulfilled', () => {
    const state = reducer(
      { ...initialState, loading: true },
      { type: 'auth/login/fulfilled', payload: 'fake-token' },
    );
    expect(state.loading).toBe(false);
    expect(state.token).toBe('fake-token');
  });

  it('should handle login.rejected', () => {
    const state = reducer(
      { ...initialState, loading: true },
      { type: 'auth/login/rejected', payload: 'Invalid credentials' },
    );
    expect(state.loading).toBe(false);
    expect(state.error).toBe('Invalid credentials');
  });
});
