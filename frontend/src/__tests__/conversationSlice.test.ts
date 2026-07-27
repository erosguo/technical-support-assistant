import { describe, it, expect } from 'vitest';
import reducer, {
  setCurrentId,
  appendMessage,
  setStreaming,
  ConversationState,
} from '../store/conversationSlice';

const initialState: ConversationState = {
  list: [],
  currentId: null,
  messages: [],
  loading: false,
  streaming: false,
};

describe('conversationSlice', () => {
  it('should return initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('should handle setCurrentId', () => {
    const state = reducer(initialState, setCurrentId('abc-123'));
    expect(state.currentId).toBe('abc-123');
  });

  it('should handle appendMessage', () => {
    const state = reducer(initialState, appendMessage({ role: 'user', content: '你好' }));
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].role).toBe('user');
    expect(state.messages[0].content).toBe('你好');
  });

  it('should handle setStreaming', () => {
    const state = reducer(initialState, setStreaming(true));
    expect(state.streaming).toBe(true);
  });

  it('should keep message history ordered', () => {
    let state = reducer(initialState, appendMessage({ role: 'user', content: 'Q1' }));
    state = reducer(state, appendMessage({ role: 'assistant', content: 'A1' }));
    state = reducer(state, appendMessage({ role: 'user', content: 'Q2' }));
    expect(state.messages).toHaveLength(3);
    expect(state.messages[0].content).toBe('Q1');
    expect(state.messages[1].content).toBe('A1');
    expect(state.messages[2].content).toBe('Q2');
  });
});
