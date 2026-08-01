import { configureStore } from '@reduxjs/toolkit';
import conversationReducer from './conversationSlice';
import authReducer from './authSlice';

export const store = configureStore({
  reducer: { conversation: conversationReducer, auth: authReducer },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export type { Citation } from './conversationSlice';
export type { AuthUser, AuthState } from './authSlice';
