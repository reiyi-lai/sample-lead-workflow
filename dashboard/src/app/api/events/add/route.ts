import { NextResponse } from "next/server";

import { getSupabaseAdmin, normalizeEventUrl } from "@/lib/supabaseServer";

interface ScoredEvent {
  event_name: string;
  event_url?: string;
  dates?: string;
  location?: string;
  venue?: string;
  cost?: string;
  description?: string;
  industry_vertical?: string;
  exhibitor_mix?: string;
  audience_mix?: string;
  source?: string;
  overall_score?: number;
  reasoning?: string;
  sales_brief?: string;
  scores?: Record<string, { score?: number; rationale?: string | string[] }>;
  [key: string]: unknown;
}

async function saveEvent(event: ScoredEvent) {
  if (!event.event_name || !event.event_url) {
    throw new Error("Enriched event is missing its name or URL");
  }

  const supabase = getSupabaseAdmin();
  const { data, error } = await supabase
    .from("events")
    .upsert(
      {
        event_name: event.event_name,
        event_url: event.event_url,
        normalized_event_url: normalizeEventUrl(event.event_url),
        dates: event.dates || null,
        location: event.location || null,
        venue: event.venue || null,
        cost: event.cost || null,
        description: event.description || null,
        industry_vertical: event.industry_vertical || null,
        exhibitor_mix: event.exhibitor_mix || null,
        audience_mix: event.audience_mix || null,
        source: event.source || "manual_add",
        overall_score: event.overall_score ?? null,
        reasoning: event.reasoning || null,
        sales_brief: event.sales_brief || null,
        raw_data: event,
      },
      { onConflict: "normalized_event_url" },
    )
    .select("id")
    .single();

  if (error) throw error;

  const { error: deleteError } = await supabase
    .from("event_score_factors")
    .delete()
    .eq("event_id", data.id);
  if (deleteError) throw deleteError;

  const factors = Object.entries(event.scores || {}).flatMap(([factorKey, factor]) => {
    if (!factor || typeof factor !== "object" || typeof factor.score !== "number") return [];
    return [{
      event_id: data.id,
      factor_key: factorKey,
      score: factor.score,
      weight: null,
      rationale: Array.isArray(factor.rationale)
        ? factor.rationale.join("\n")
        : factor.rationale || "",
    }];
  });

  if (factors.length) {
    const { error: factorError } = await supabase.from("event_score_factors").insert(factors);
    if (factorError) throw factorError;
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const pipelineApiUrl = process.env.PIPELINE_API_URL || "http://localhost:8000";
    const response = await fetch(`${pipelineApiUrl}/api/events/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (!response.ok) {
      const message = await response.text();
      return NextResponse.json(
        { error: `Pipeline API error: ${message || response.status}` },
        { status: response.status },
      );
    }

    const result = await response.json();
    const events = (result.events || []) as ScoredEvent[];
    await Promise.all(events.map(saveEvent));

    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
