import api from './api';

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
  const res = await api.post('/tickets', data);
  return res.data;
}

export async function listTickets(): Promise<TicketListItem[]> {
  const res = await api.get('/tickets');
  return res.data;
}

export async function getTicket(id: string): Promise<Ticket> {
  const res = await api.get(`/tickets/${id}`);
  return res.data;
}

export async function updateTicket(id: string, data: UpdateTicketRequest): Promise<Ticket> {
  const res = await api.patch(`/tickets/${id}`, data);
  return res.data;
}

export async function deleteTicket(id: string): Promise<void> {
  await api.delete(`/tickets/${id}`);
}
