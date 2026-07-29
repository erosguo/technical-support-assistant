import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export interface DiagnosisMatch {
  id: string;
  pattern: string;
  solution: string | null;
  severity: string;
  category: string | null;
  tags: string[];
}

export interface DiagnosisResult {
  reply: string;
  matches: DiagnosisMatch[];
  needs_escalation: boolean;
  conversation_id: string | null;
}

export async function diagnose(errorText: string): Promise<DiagnosisResult> {
  const res = await axios.post(`${API_BASE}/diagnosis`, {
    error_text: errorText,
  });
  return res.data;
}
