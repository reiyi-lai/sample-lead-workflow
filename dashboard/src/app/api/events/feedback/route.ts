import { NextResponse } from "next/server";

import { findEventId, getSupabaseAdmin } from "@/lib/supabaseServer";

interface FeedbackRow {
  would_attend_again: boolean | null;
  notes: string;
  events: { event_url: string | null } | Array<{ event_url: string | null }> | null;
}

export async function GET() {
  try {
    const { data, error } = await getSupabaseAdmin()
      .from("event_feedback")
      .select("would_attend_again, notes, events!inner(event_url)");

    if (error) throw error;

    const feedback: Record<string, { would_attend_again: boolean | null; notes: string }> = {};
    for (const row of (data || []) as FeedbackRow[]) {
      const event = Array.isArray(row.events) ? row.events[0] : row.events;
      if (!event?.event_url) continue;
      feedback[event.event_url] = {
        would_attend_again: row.would_attend_again,
        notes: row.notes,
      };
    }

    return NextResponse.json(feedback);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const { event_url, would_attend_again = null, notes = "" } = await request.json();
    if (!event_url) {
      return NextResponse.json({ error: "event_url is required" }, { status: 400 });
    }

    const eventId = await findEventId(event_url);
    if (!eventId) {
      return NextResponse.json({ error: "Event not found" }, { status: 404 });
    }

    const { data, error } = await getSupabaseAdmin()
      .from("event_feedback")
      .upsert(
        { event_id: eventId, would_attend_again, notes: String(notes) },
        { onConflict: "event_id" },
      )
      .select("would_attend_again, notes")
      .single();

    if (error) throw error;
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
