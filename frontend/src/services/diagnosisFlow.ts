import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

function getToken(): string | null {
  return localStorage.getItem('tech_support_token');
}

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}` };
}

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
  const res = await axios.get(`${API_BASE}/diagnosis/flows`, { headers: authHeaders() });
  return res.data;
}

export async function getFlow(id: string): Promise<DiagnosisFlow> {
  const res = await axios.get(`${API_BASE}/diagnosis/flows/${id}`, { headers: authHeaders() });
  return res.data;
}

export async function createFlow(data: { name: string; description: string; steps: FlowStep[] }): Promise<DiagnosisFlow> {
  const res = await axios.post(`${API_BASE}/diagnosis/flows`, data, { headers: authHeaders() });
  return res.data;
}

export async function updateFlow(id: string, data: Partial<{ name: string; description: string; steps: FlowStep[]; is_active: boolean }>): Promise<DiagnosisFlow> {
  const res = await axios.patch(`${API_BASE}/diagnosis/flows/${id}`, data, { headers: authHeaders() });
  return res.data;
}

export async function deleteFlow(id: string): Promise<void> {
  await axios.delete(`${API_BASE}/diagnosis/flows/${id}`, { headers: authHeaders() });
}

export async function activateFlow(id: string): Promise<DiagnosisFlow> {
  const res = await axios.post(`${API_BASE}/diagnosis/flows/${id}/activate`, {}, { headers: authHeaders() });
  return res.data;
}
