import { supabase } from './lib/supabase';

const API = '/api';

async function authHeaders(extra = {}) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return {
    ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function handleJson(res, fallbackMessage) {
  if (!res.ok) {
    let message = fallbackMessage;
    try {
      const err = await res.json();
      message = err?.detail?.error || err?.error || fallbackMessage;
    } catch {
      // keep fallback message
    }
    throw new Error(message);
  }
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API}/documents`, { headers: await authHeaders() });
  return handleJson(res, 'โหลดรายการเอกสารไม่สำเร็จ');
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append('originalName', file.name);
  form.append('file', file);

  const res = await fetch(`${API}/documents`, {
    method: 'POST',
    headers: await authHeaders(),
    body: form,
  });
  return handleJson(res, 'อัปโหลดไม่สำเร็จ');
}

export async function updateDocumentType(id, docType) {
  const res = await fetch(`${API}/documents/${id}`, {
    method: 'PATCH',
    headers: await authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ docType }),
  });
  return handleJson(res, 'เปลี่ยนประเภทไม่สำเร็จ');
}

export async function deleteDocument(id) {
  const res = await fetch(`${API}/documents/${id}`, {
    method: 'DELETE',
    headers: await authHeaders(),
  });
  return handleJson(res, 'ลบเอกสารไม่สำเร็จ');
}
