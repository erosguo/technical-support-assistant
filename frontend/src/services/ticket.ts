import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export interface Ticket {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListItem {
  id: string;
  title: string;
  status: string;
  priority: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTicketRequest {
  title: string;
  description?: string;
  priority?: string;
}

export interface UpdateTicketRequest {
  status?: string;
  priority?: string;
  assigned_to?: string;
}

export async function createTicket(data: CreateTicketRequest): Promise<Ticket> {
  const res = await axios.post(`${API_BASE}/tickets`, data);
  return res.data;
}

export async function listTickets(): Promise<TicketListItem[]> {
  const res = await axios.get(`${API_BASE}/tickets`);
  return res.data;
}

export async function getTicket(id: string): Promise<Ticket> {
  const res = await axios.get(`${API_BASE}/tickets/${id}`);
  return res.data;
}

export async function updateTicket(id: string, data: UpdateTicketRequest): Promise<Ticket> {
  const res = await axios.patch(`${API_BASE}/tickets/${id}`, data);
  return res.data;
}

export async function deleteTicket(id: string): Promise<void> {
  await axios.delete(`${API_BASE}/tickets/${id}`);
}
