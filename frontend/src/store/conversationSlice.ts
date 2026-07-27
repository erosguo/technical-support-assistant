import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export interface Citation {
  document_id: string;
  document_title: string;
  chunk_index: number;
  score: number;
  excerpt: string;
}

export interface Message {
  id: string;
  role: string;
  content: string;
  agent_name?: string;
  sources?: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationState {
  list: Conversation[];
  currentId: string | null;
  messages: Message[];
  loading: boolean;
  streaming: boolean;
}

const initialState: ConversationState = {
  list: [],
  currentId: null,
  messages: [],
  loading: false,
  streaming: false,
};

export const fetchConversations = createAsyncThunk('conversation/fetchList', async () => {
  const res = await axios.get(`${API_BASE}/chat/conversations`);
  return res.data;
});

export const createConversation = createAsyncThunk(
  'conversation/create',
  async (title?: string) => {
    const res = await axios.post(`${API_BASE}/chat/conversations`, {
      title: title || '新对话',
    });
    return res.data;
  },
);

export const fetchMessages = createAsyncThunk(
  'conversation/fetchMessages',
  async (convId: string) => {
    const res = await axios.get(`${API_BASE}/chat/conversations/${convId}/messages`);
    return res.data;
  },
);

const slice = createSlice({
  name: 'conversation',
  initialState,
  reducers: {
    setCurrentId(state, action: PayloadAction<string>) {
      state.currentId = action.payload;
    },
    appendMessage(
      state,
      action: PayloadAction<{ role: string; content: string; sources?: Citation[] }>,
    ) {
      state.messages.push({
        id: Date.now().toString(),
        role: action.payload.role,
        content: action.payload.content,
        sources: action.payload.sources,
        created_at: new Date().toISOString(),
      });
    },
    setStreaming(state, action: PayloadAction<boolean>) {
      state.streaming = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchConversations.fulfilled, (state, action) => {
      state.list = action.payload;
    });
    builder.addCase(createConversation.fulfilled, (state, action) => {
      state.list.unshift(action.payload);
      state.currentId = action.payload.id;
      state.messages = [];
    });
    builder.addCase(fetchMessages.fulfilled, (state, action) => {
      state.messages = action.payload;
    });
  },
});

export const { setCurrentId, appendMessage, setStreaming } = slice.actions;
export default slice.reducer;
