import api from './api';

export interface FlowStep {
  id: string;
  title: string;
  description?: string;
  conditions?: any[];
  next_step?: string | null;
}

export interface DiagnosisFlow {
  id: string;
  name: string;
  description: string | null;
  steps: FlowStep[];
  version: number;
  is_active: boolean;
}

export async function listFlows(): Promise<DiagnosisFlow[]> {
  const res = await api.get('/diagnosis/flows');
  return res.data;
}

export async function getFlow(id: string): Promise<DiagnosisFlow> {
  const res = await api.get(`/diagnosis/flows/${id}`);
  return res.data;
}

export async function createFlow(data: { name: string; description: string; steps: FlowStep[] }): Promise<DiagnosisFlow> {
  const res = await api.post('/diagnosis/flows', data);
  return res.data;
}

export async function updateFlow(id: string, data: Partial<{ name: string; description: string; steps: FlowStep[]; is_active: boolean }>): Promise<DiagnosisFlow> {
  const res = await api.patch(`/diagnosis/flows/${id}`, data);
  return res.data;
}

export async function deleteFlow(id: string): Promise<void> {
  await api.delete(`/diagnosis/flows/${id}`);
}

export async function activateFlow(id: string): Promise<DiagnosisFlow> {
  const res = await api.post(`/diagnosis/flows/${id}/activate`, {});
  return res.data;
}
