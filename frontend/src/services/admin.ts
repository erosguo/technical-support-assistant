import api from './api';

export interface SystemStats {
  total_conversations: number;
  total_messages: number;
  total_documents: number;
  total_tickets: number;
  tickets_by_status: Record<string, number>;
  users_by_role: Record<string, number>;
}

export interface QualityScore {
  relevance: number;
  accuracy: number;
  completeness: number;
  clarity: number;
  overall: number;
}

export async function getSystemStats(): Promise<SystemStats> {
  const res = await api.get('/admin/stats');
  return res.data;
}

export async function evaluateResponse(data: { response: string; context?: string }): Promise<QualityScore> {
  const res = await api.post('/admin/evaluate', data);
  return res.data;
}

export async function discoverKnowledge(): Promise<{ patterns: Array<{ id: string; pattern: string; solution: string; severity: string; category: string; created_at: string }> }> {
  const res = await api.post('/admin/discover', {});
  return res.data;
}