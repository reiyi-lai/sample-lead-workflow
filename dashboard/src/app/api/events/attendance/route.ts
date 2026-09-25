import { NextResponse } from "next/server";

import { findEventId, getSupabaseAdmin } from "@/lib/supabaseServer";

interface AttendanceRow {
  attending: boolean;
  whos_going: string[];
  events: { event_url: string | null } | Array<{ event_url: string | null }> | null;
}

export async function GET() {
  try {
    const { data, error } = await getSupabaseAdmin()
      .from("event_attendance")
      .select("attending, whos_going, events!inner(event_url)");

    if (error) throw error;

    const attendance: Record<string, { attending: boolean; whos_going: string }> = {};
    for (const row of (data || []) as AttendanceRow[]) {
      const event = Array.isArray(row.events) ? row.events[0] : row.events;
      if (!event?.event_url) continue;
      attendance[event.event_url] = {
        attending: row.attending,
        whos_going: (row.whos_going || []).join("\n"),
      };
    }

    return NextResponse.json(attendance);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const { event_url, attending, whos_going = "" } = await request.json();
    if (!event_url || typeof attending !== "boolean") {
      return NextResponse.json(
        { error: "event_url and attending are required" },
        { status: 400 },
      );
    }

    const eventId = await findEventId(event_url);
    if (!eventId) {
      return NextResponse.json({ error: "Event not found" }, { status: 404 });
    }

    const attendees = String(whos_going)
      .split(/[,;\n]+/)
      .map((name) => name.trim())
      .filter(Boolean);
    const { data, error } = await getSupabaseAdmin()
      .from("event_attendance")
      .upsert({ event_id: eventId, attending, whos_going: attendees }, { onConflict: "event_id" })
      .select("attending, whos_going")
      .single();

    if (error) throw error;
    return NextResponse.json({
      attending: data.attending,
      whos_going: (data.whos_going || []).join("\n"),
    });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
