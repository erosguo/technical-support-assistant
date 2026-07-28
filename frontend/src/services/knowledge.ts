import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1/knowledge';

export interface DocumentSummary {
  id: string;
  title: string;
  doc_type: string;
  created_at: string;
}

export interface DocumentDetail extends DocumentSummary {
  content: string;
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  const res = await axios.get(`${API_BASE}/documents`);
  return res.data;
}

export async function uploadDocument(
  title: string,
  file: File,
): Promise<{ id: string; title: string }> {
  const form = new FormData();
  form.append('title', title);
  form.append('file', file);
  const res = await axios.post(`${API_BASE}/documents`, form);
  return res.data;
}

export async function getDocument(id: string): Promise<DocumentDetail> {
  const res = await axios.get(`${API_BASE}/documents/${id}`);
  return res.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await axios.delete(`${API_BASE}/documents/${id}`);
}
