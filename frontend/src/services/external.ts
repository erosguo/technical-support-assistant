import api from './api';

export async function syncTicketToExternal(
  ticketId: string,
  provider: string,
  config?: Record<string, any>,
): Promise<{ external_id: string; provider: string; url: string }> {
  const res = await api.post(`/external/sync`, { ticket_id: ticketId, provider, config });
  return res.data;
}

export async function getExternalConfig(provider: string): Promise<Record<string, any>> {
  const res = await api.get(`/external/config/${provider}`);
  return res.data;
}