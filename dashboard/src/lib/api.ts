const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function addEvents(events: { event_name: string; event_url: string }[]) {
  return apiFetch("/api/events/add", {
    method: "POST",
    body: JSON.stringify({ events }),
  });
}

export async function getAttendance(): Promise<Record<string, { attending: boolean; whos_going: string }>> {
  return apiFetch("/api/events/attendance");
}

export async function updateAttendance(event_url: string, attending: boolean, whos_going: string) {
  return apiFetch("/api/events/attendance", {
    method: "POST",
    body: JSON.stringify({ event_url, attending, whos_going }),
  });
}

export async function getFeedback(): Promise<Record<string, { would_attend_again: boolean | null; notes: string }>> {
  return apiFetch("/api/events/feedback");
}

export async function updateFeedback(event_url: string, would_attend_again: boolean | null, notes: string) {
  return apiFetch("/api/events/feedback", {
    method: "POST",
    body: JSON.stringify({ event_url, would_attend_again, notes }),
  });
}
