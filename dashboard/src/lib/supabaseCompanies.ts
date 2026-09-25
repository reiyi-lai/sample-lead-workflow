import "server-only";

import type { CompanyScoring, CompanyWithDetails, ContactWithOutreach, OutreachMessage } from "@/lib/data";
import { getSupabaseAdmin } from "@/lib/supabaseServer";

interface CompanyRow {
  id: string;
  company_name: string;
  website_url: string | null;
  overall_score: number | null;
  qualification_summary: string | null;
  company_score_factors: Array<{ factor_key: string; score: number; rationale: string[] }>;
  target_roles: Array<{
    id: string;
    title: string;
    priority: number;
    rationale: string;
    linkedin_searches: { search_url: string } | Array<{ search_url: string }> | null;
  }>;
  contacts: Array<{
    id: string;
    target_role_id: string | null;
    full_name: string;
    title: string | null;
    email: string | null;
    linkedin_url: string | null;
  }>;
  outreach_generation: Array<{
    id: string;
    target_role_id: string | null;
    contact_id: string | null;
    channel: string;
    subject: string | null;
    body: string;
    status: string;
    engagement_strategy: Record<string, string> | null;
  }>;
  event_companies: Array<{
    confidence: string;
    events: { event_name: string } | Array<{ event_name: string }> | null;
  }>;
}

function getEventName(relationship: CompanyRow["event_companies"][number]): string | null {
  const event = Array.isArray(relationship.events) ? relationship.events[0] : relationship.events;
  return event?.event_name || null;
}

function toOutreach(draft: CompanyRow["outreach_generation"][number] | undefined, name?: string): OutreachMessage | null {
  if (!draft) return null;
  const personalize = (value: string) => name ? value.replaceAll("[Name]", name) : value;
  return {
    channel: draft.channel,
    message: {
      subject: draft.subject ? personalize(draft.subject) : undefined,
      body: personalize(draft.body),
    },
    status: draft.status === "sent" ? "sent" : "draft",
  };
}

function toCompany(row: CompanyRow): CompanyWithDetails {
  const roles = row.target_roles || [];
  const drafts = row.outreach_generation || [];
  const storedContacts = row.contacts || [];
  const events = [...new Set((row.event_companies || []).map(getEventName).filter((name): name is string => Boolean(name)))];
  const scores: CompanyScoring["scores"] = {};
  for (const factor of row.company_score_factors || []) {
    if (factor.factor_key === "industry_fit" || factor.factor_key === "size_revenue_fit" ||
        factor.factor_key === "strategic_relevance" || factor.factor_key === "market_activity") {
      scores[factor.factor_key] = { score: Number(factor.score), rationale: factor.rationale };
    }
  }

  const contacts: ContactWithOutreach[] = [];
  for (const role of roles) {
    const roleContacts = storedContacts.filter((contact) => contact.target_role_id === role.id);
    const roleDraft = drafts.find((draft) => draft.target_role_id === role.id && !draft.contact_id);
    if (roleContacts.length === 0) {
      contacts.push({
        name: "[Name]",
        title: role.title,
        company: row.company_name,
        companyId: row.id,
        roleId: role.id,
        analysis: null,
        outreach: toOutreach(roleDraft),
      });
    } else {
      for (const contact of roleContacts) {
        const contactDraft = drafts.find((draft) => draft.contact_id === contact.id);
        contacts.push({
          name: contact.full_name,
          title: role.title,
          company: row.company_name,
          companyId: row.id,
          roleId: role.id,
          contactId: contact.id,
          email: contact.email || undefined,
          linkedinUrl: contact.linkedin_url || undefined,
          analysis: null,
          outreach: toOutreach(contactDraft || roleDraft, contact.full_name),
        });
      }
    }
  }

  for (const contact of storedContacts.filter((item) => !item.target_role_id || !roles.some((role) => role.id === item.target_role_id))) {
    const draft = drafts.find((item) => item.contact_id === contact.id);
    contacts.push({
      name: contact.full_name,
      title: contact.title || "Contact",
      company: row.company_name,
      companyId: row.id,
      contactId: contact.id,
      email: contact.email || undefined,
      linkedinUrl: contact.linkedin_url || undefined,
      analysis: null,
      outreach: toOutreach(draft, contact.full_name),
    });
  }

  return {
    id: row.id,
    name: row.company_name,
    event: events[0] || "",
    events,
    attendanceType: row.event_companies?.[0]?.confidence === "confirmed" ? "Confirmed" : "Likely",
    score: row.overall_score == null ? 0 : Number(row.overall_score),
    qualificationSummary: row.qualification_summary || "",
    scoring: {
      company_name: row.company_name,
      website_url: row.website_url || undefined,
      scores,
      qualification_summary: row.qualification_summary || undefined,
      icp_qualification: { weighted_score: Number(row.overall_score || 0) },
    },
    targetRoles: roles.length ? {
      company_name: row.company_name,
      target_roles: roles.map(({ title, priority, rationale }) => ({ title, priority, rationale })),
    } : null,
    linkedInSearches: roles.flatMap((role) => {
      const searches = Array.isArray(role.linkedin_searches)
        ? role.linkedin_searches
        : role.linkedin_searches ? [role.linkedin_searches] : [];
      return searches.map((search) => ({ role_title: role.title, search_url: search.search_url }));
    }),
    contacts,
  };
}

export async function getSupabaseCompaniesWithDetails(): Promise<CompanyWithDetails[]> {
  const rows: CompanyRow[] = [];
  for (let offset = 0; ; offset += 1000) {
    const { data, error } = await getSupabaseAdmin()
      .from("companies")
      .select(`
        id, company_name, website_url, overall_score, qualification_summary,
        company_score_factors(factor_key, score, rationale),
        target_roles(id, title, priority, rationale, linkedin_searches(search_url)),
        contacts(id, target_role_id, full_name, title, email, linkedin_url),
        outreach_generation(id, target_role_id, contact_id, channel, subject, body, status, engagement_strategy),
        event_companies(confidence, events(event_name))
      `)
      .order("overall_score", { ascending: false, nullsFirst: false })
      .range(offset, offset + 999);
    if (error) throw new Error(`Failed to load companies from Supabase: ${error.message}`);
    const page = (data || []) as unknown as CompanyRow[];
    rows.push(...page);
    if (page.length < 1000) break;
  }
  return rows.map(toCompany);
}

export async function getSupabaseCompanyStats(companies: CompanyWithDetails[]) {
  const { count, error } = await getSupabaseAdmin().from("events").select("id", { count: "exact", head: true });
  if (error) throw new Error(`Failed to count events in Supabase: ${error.message}`);
  return {
    events: count || 0,
    companies: companies.length,
    contacts: companies.reduce((sum, company) => sum + company.contacts.filter((contact) => contact.contactId).length, 0),
    messages: companies.reduce((sum, company) => sum + company.contacts.filter((contact) => contact.outreach).length, 0),
  };
}
