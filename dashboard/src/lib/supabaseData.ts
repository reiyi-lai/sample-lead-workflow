import "server-only";

import type { Company, Event, EventScores } from "@/lib/data";
import { getSupabaseAdmin } from "@/lib/supabaseServer";

interface EventRow extends Event {
  id: string;
  event_score_factors: Array<{
    factor_key: string;
    score: number;
    rationale: string;
  }>;
  event_companies: Array<{
    attendance_type: string;
    confidence: string;
    booth_number: string | null;
    raw_data: { company_name?: string } | null;
    companies: {
      company_name: string;
      website_url: string | null;
    } | Array<{
      company_name: string;
      website_url: string | null;
    }> | null;
  }>;
}

export interface SupabaseEvent extends Event {
  companies: Company[];
  totalConfirmed: number;
  totalLikely: number;
}

export async function getSupabaseEvents(): Promise<SupabaseEvent[]> {
  const { data, error } = await getSupabaseAdmin()
    .from("events")
    .select(`
      id,
      event_name,
      event_url,
      dates,
      location,
      venue,
      cost,
      description,
      industry_vertical,
      exhibitor_mix,
      audience_mix,
      overall_score,
      reasoning,
      sales_brief,
      event_score_factors(factor_key, score, rationale),
      event_companies(
        attendance_type,
        confidence,
        booth_number,
        raw_data,
        companies(company_name, website_url)
      )
    `)
    .order("overall_score", { ascending: false, nullsFirst: false });

  if (error) throw new Error(`Failed to load events from Supabase: ${error.message}`);

  return ((data || []) as unknown as EventRow[]).map((row) => {
    const scores = row.event_score_factors.reduce<EventScores>((result, factor) => {
      result[factor.factor_key] = {
        score: Number(factor.score),
        rationale: factor.rationale,
      };
      return result;
    }, {});

    const companies = row.event_companies.flatMap((relationship) => {
      const company = Array.isArray(relationship.companies)
        ? relationship.companies[0]
        : relationship.companies;
      if (!company) return [];
      return [{
        company_name: relationship.raw_data?.company_name || company.company_name,
        website_url: company.website_url || undefined,
        attendance_type: relationship.attendance_type,
        confidence: relationship.confidence,
      }];
    });

    return {
      event_name: row.event_name,
      event_url: row.event_url,
      dates: row.dates,
      location: row.location,
      venue: row.venue,
      cost: row.cost,
      description: row.description,
      industry_vertical: row.industry_vertical,
      exhibitor_mix: row.exhibitor_mix,
      audience_mix: row.audience_mix,
      overall_score: row.overall_score == null ? undefined : Number(row.overall_score),
      reasoning: row.reasoning,
      sales_brief: row.sales_brief,
      scores,
      companies,
      totalConfirmed: companies.filter((company) => company.confidence === "confirmed").length,
      totalLikely: companies.filter((company) => company.confidence === "likely").length,
    };
  });
}
