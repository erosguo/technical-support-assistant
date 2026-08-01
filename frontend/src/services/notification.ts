import api from './api';

export async function sendNotification(
  provider: string,
  webhookUrl: string,
  title: string,
  content: string,
): Promise<{ success: boolean; message: string }> {
  const res = await api.post('/notifications/send', { provider, webhook_url: webhookUrl, title, content });
  return res.data;
}

export async function sendEscalation(
  provider: string,
  webhookUrl: string,
  ticketTitle: string,
  ticketDescription: string,
): Promise<{ success: boolean; message: string }> {
  const res = await api.post('/notifications/escalation', {
    provider,
    webhook_url: webhookUrl,
    ticket_title: ticketTitle,
    ticket_description: ticketDescription,
  });
  return res.data;
}