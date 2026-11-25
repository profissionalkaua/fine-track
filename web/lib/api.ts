export type Identity = {
  user: { id: string; email: string; country: string };
  workspace: { id: string; name: string; role: 'owner' | 'editor' | 'viewer' };
  csrf_token: string;
};
export type Video = {
  id: string; creator_id: string; handle: string; description: string;
  url: string | null; thumbnail: string | null; published_at: string; observed_at: string;
  country: string | null; geo_evidence: { kind: string; reason: string; confidence: number };
  hashtags: { key: string; label: string }[]; categories: { text: string; confidence: number }[];
  duration: number | null; synthetic: boolean; rank?: number;
  views: number | null; likes: number | null; comments: number | null; shares: number | null;
  velocity?: number; delta_views?: number; partial_window?: boolean;
};
export type FeedData = {
  items: Video[]; country: string; period: string; category: string | null;
  coverage_status: string; eligible_count: number; as_of: string | null; cursor: string | null;
  version: string | null; most_viewed: Video[]; window_start: string; window_end: string;
  is_stale: boolean; reason: string | null;
};
let csrf = '';
export function setSession(identity: Identity | null) { csrf = identity?.csrf_token || ''; }

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...options, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf, ...options.headers },
  });
  if (!response.ok) {
    let message = `Não foi possível concluir a operação (${response.status}).`;
    try { const error = await response.json(); if (typeof error.detail === 'string') message = error.detail; } catch {}
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function metric(value: number | null | undefined): string {
  return value == null ? 'Indisponível' : new Intl.NumberFormat('pt-BR', {
    notation: value >= 10000 ? 'compact' : 'standard', maximumFractionDigits: 1,
  }).format(value);
}

export function date(value: string | null | undefined, time = true): string {
  return value ? new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit', month: 'short', ...(time ? { hour: '2-digit', minute: '2-digit' } : {}),
    timeZone: 'America/Sao_Paulo',
  }).format(new Date(value)) : 'Ainda sem atualização';
}
