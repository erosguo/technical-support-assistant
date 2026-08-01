import api from './api';

export interface UserSummary {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

export async function listUsers(): Promise<UserSummary[]> {
  const res = await api.get('/users');
  return res.data;
}

export async function createUser(data: { email: string; name: string; password: string; role: string }): Promise<UserSummary> {
  const res = await api.post('/users', data);
  return res.data;
}

export async function updateUser(id: string, data: { name?: string; role?: string; is_active?: boolean }): Promise<UserSummary> {
  const res = await api.patch(`/users/${id}`, data);
  return res.data;
}

export async function deleteUser(id: string): Promise<void> {
  await api.delete(`/users/${id}`);
}