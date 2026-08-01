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

export async function evaluateResponse(data: { query: string; response: string }): Promise<QualityScore> {
  const res = await api.post('/admin/quality/evaluate', data);
  return res.data;
}

export async function discoverKnowledge(minTickets: number = 2): Promise<any[]> {
  const res = await api.post('/admin/knowledge/discover', null, { params: { min_tickets: minTickets } });
  return res.data;
}
