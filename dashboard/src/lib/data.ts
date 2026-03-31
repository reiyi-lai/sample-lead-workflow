import fs from 'fs';
import path from 'path';

const DATA_DIR = path.join(process.cwd(), 'data');

export interface EventScore {
  score: number;
  rationale: string;
}

export interface EventScores {
  industry_alignment?: EventScore;
  scale_timing?: EventScore;
  buyer_quality?: EventScore;
  buyer_intent_alignment?: EventScore;
}

export interface Event {
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
  overall_score?: number;
  scores?: EventScores;
  reasoning?: string;
  sales_brief?: string;
}

export interface ScoredEvents {
  scored_events: Event[];
  summary: {
    total_events_scored: number;
  };
}

export interface Company {
  company_name: string;
  company_url?: string;
  website_url?: string;
  attendance_type?: string;
  event_name?: string;
  source?: string;
  confidence?: string;
}

export interface CompanyDiscovery {
  event_name: string;
  event_url?: string;
  success: boolean;
  companies: Company[];
  total_confirmed?: number;
  total_likely?: number;
}

export interface CompanyScoring {
  company_name?: string;
  website_url?: string;
  scores: {
    industry_fit?: { score: number; rationale: string };
    size_revenue_fit?: { score: number; rationale: string };
    strategic_relevance?: { score: number; rationale: string };
    market_activity?: { score: number; rationale: string };
  };
  qualification_summary?: string;
  icp_qualification?: {
    weighted_score: number;
  };
}

export interface TargetRole {
  title: string;
  priority: number;
  rationale: string;
}

export interface TargetRoles {
  company_name: string;
  target_roles: TargetRole[];
}

export interface LinkedInSearch {
  role_title: string;
  search_url: string;
}

export interface ContactAnalysis {
  contact_name?: string;
  full_name?: string;
  title?: string;
  company_name?: string;
  engagement_strategy?: Record<string, string>;
  recommended_channel?: string;
}

export interface OutreachMessage {
  channel?: string;
  message?: {
    subject?: string;
    body?: string;
  };
  status?: 'draft' | 'sent';
}

export interface CompanyWithDetails {
  name: string;
  event: string;
  attendanceType: string;
  score: number;
  qualificationSummary: string;
  scoring: CompanyScoring | null;
  targetRoles: TargetRoles | null;
  linkedInSearches: LinkedInSearch[];
  contacts: ContactWithOutreach[];
}

export interface ContactWithOutreach {
  name: string;
  title: string;
  company: string;
  analysis: ContactAnalysis | null;
  outreach: OutreachMessage | null;
}

// DATA LOADING FUNCTIONS

function safeReadJson<T>(filePath: string): T | null {
  try {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content) as T;
    }
  } catch (error) {
    console.error(`Error reading ${filePath}:`, error);
  }
  return null;
}

// Normalize company name for matching (removes Inc., Corp., LLC, etc.)
function normalizeCompanyName(name: string): string {
  return name
    .replace(/,?\s*(Inc\.?|Corp\.?|LLC|Ltd\.?|Corporation|Company|Co\.?)$/i, '')
    .replace(/[^\w\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

// Find matching company folder by fuzzy matching
function findCompanyFolder(companyName: string, folders: string[]): string | null {
  const normalizedSearch = normalizeCompanyName(companyName);

  // Try exact match first
  for (const folder of folders) {
    if (normalizeCompanyName(folder) === normalizedSearch) {
      return folder;
    }
  }

  // Try contains match
  for (const folder of folders) {
    const normalizedFolder = normalizeCompanyName(folder);
    if (normalizedFolder.includes(normalizedSearch) || normalizedSearch.includes(normalizedFolder)) {
      return folder;
    }
  }

  return null;
}

// Get all discovered events
export function getDiscoveredEvents(): Event[] {
  const filePath = path.join(DATA_DIR, 'events', 'discovered_events.json');
  return safeReadJson<Event[]>(filePath) || [];
}

// Get scored events
export function getScoredEvents(): ScoredEvents | null {
  const filePath = path.join(DATA_DIR, 'events', 'scored_events.json');
  return safeReadJson<ScoredEvents>(filePath);
}

// Get companies discovered at events (reads per-event files from events/)
export function getEventCompanies(): CompanyDiscovery[] {
  const eventsDir = path.join(DATA_DIR, 'events');
  const excludedFiles = new Set(['discovered_events.json', 'scored_events.json', 'discovered_companies.json', 'pipeline_summary.json']);
  const results: CompanyDiscovery[] = [];

  try {
    if (fs.existsSync(eventsDir)) {
      const files = fs.readdirSync(eventsDir).filter(f => f.endsWith('.json') && !excludedFiles.has(f));
      for (const file of files) {
        const data = safeReadJson<CompanyDiscovery>(path.join(eventsDir, file));
        if (data && data.companies) {
          results.push(data);
        }
      }
    }
  } catch (error) {
    console.error('Error reading event companies folder:', error);
  }

  return results;
}

// Read folder listings fresh on every request (no caching)
// so new data from the pipeline is visible immediately.

function getCompanyFolders(): string[] {
  const companiesDir = path.join(DATA_DIR, 'companies');
  try {
    if (fs.existsSync(companiesDir)) {
      return fs.readdirSync(companiesDir).filter(f => {
        const stat = fs.statSync(path.join(companiesDir, f));
        return stat.isDirectory();
      });
    }
  } catch {}
  return [];
}

// Get company scoring
export function getCompanyScoring(companyName: string): CompanyScoring | null {
  const folders = getCompanyFolders();
  const folder = findCompanyFolder(companyName, folders);
  if (!folder) return null;

  const filePath = path.join(DATA_DIR, 'companies', folder, 'scoring.json');
  return safeReadJson<CompanyScoring>(filePath);
}

// Get target roles for a company
export function getTargetRoles(companyName: string): TargetRoles | null {
  const folders = getCompanyFolders();
  const folder = findCompanyFolder(companyName, folders);
  if (!folder) return null;

  const filePath = path.join(DATA_DIR, 'companies', folder, 'target_roles.json');
  return safeReadJson<TargetRoles>(filePath);
}

export function getLinkedInSearches(companyName: string): LinkedInSearch[] {
  const folders = getCompanyFolders();
  const folder = findCompanyFolder(companyName, folders);
  if (!folder) return [];

  const filePath = path.join(DATA_DIR, 'companies', folder, 'linkedin_searches.json');
  return safeReadJson<LinkedInSearch[]>(filePath) || [];
}

// Get role-based outreach (auto-generated from Stage 4)
// Mirror Python's sanitize_name(): remove special chars, keep \w\s-, collapse spaces
function sanitizeName(name: string): string {
  return name.replace(/[^\w\s-]/g, '').replace(/\s+/g, ' ').trim();
}

function roleFilePrefix(title: string): string {
  return sanitizeName(title).replace(/ /g, '_');
}

export function getRoleAnalysis(companyName: string, roleTitle: string): ContactAnalysis | null {
  const folders = getCompanyFolders();
  const folder = findCompanyFolder(companyName, folders);
  if (!folder) return null;

  const prefix = roleFilePrefix(roleTitle);
  const filePath = path.join(DATA_DIR, 'companies', folder, 'roles', `${prefix}_analysis.json`);
  return safeReadJson<ContactAnalysis>(filePath);
}

export function getRoleOutreach(companyName: string, roleTitle: string): OutreachMessage | null {
  const folders = getCompanyFolders();
  const folder = findCompanyFolder(companyName, folders);
  if (!folder) return null;

  const prefix = roleFilePrefix(roleTitle);
  const filePath = path.join(DATA_DIR, 'companies', folder, 'roles', `${prefix}_outreach.json`);
  return safeReadJson<OutreachMessage>(filePath);
}

// Get all contacts/roles for a company (reads from companies/{co}/roles/)
export function getCompanyContacts(companyName: string): ContactWithOutreach[] {
  const folders = getCompanyFolders();
  const folder = findCompanyFolder(companyName, folders);
  if (!folder) return [];

  const rolesDir = path.join(DATA_DIR, 'companies', folder, 'roles');
  const contacts: ContactWithOutreach[] = [];

  try {
    if (!fs.existsSync(rolesDir)) return [];

    const files = fs.readdirSync(rolesDir).filter(f => f.endsWith('_analysis.json'));
    for (const file of files) {
      const roleName = file.replace('_analysis.json', '').replace(/_/g, ' ');
      const analysis = safeReadJson<ContactAnalysis>(path.join(rolesDir, file));
      const outreachFile = file.replace('_analysis.json', '_outreach.json');
      const outreach = safeReadJson<OutreachMessage>(path.join(rolesDir, outreachFile));

      if (analysis) {
        contacts.push({
          name: analysis.full_name || analysis.contact_name || roleName,
          title: analysis.title || roleName,
          company: companyName,
          analysis,
          outreach,
        });
      }
    }
  } catch (error) {
    console.error(`Error reading roles for ${companyName}:`, error);
  }

  return contacts;
}

// Normalize URL for deduplication (same logic as Python pipeline)
function normalizeUrl(url: string): string {
  return (url || '').toLowerCase().replace('://www.', '://').replace(/\/$/, '');
}

// Get all companies with full details (event-driven, deduplicated by URL and name)
export function getAllCompaniesWithDetails(): CompanyWithDetails[] {
  const eventCompanies = getEventCompanies();
  const companyMap = new Map<string, CompanyWithDetails>();
  // Track by both URL and normalized name to deduplicate
  const seenUrls = new Set<string>();
  const seenNames = new Set<string>();

  // Build company list from event discoveries, deduplicate by URL OR name
  for (const eventDiscovery of eventCompanies) {
    for (const company of eventDiscovery.companies || []) {
      const name = company.company_name;
      if (!name) continue;

      const url = normalizeUrl(company.website_url || '');
      const normalizedName = name.toLowerCase().trim();

      // Skip if we've seen this URL or this exact company name
      if ((url && seenUrls.has(url)) || seenNames.has(normalizedName)) continue;

      if (url) seenUrls.add(url);
      seenNames.add(normalizedName);

      const dedupeKey = url || `name:${normalizedName}`;

      const scoring = getCompanyScoring(name);
      const targetRoles = getTargetRoles(name);
      const linkedInSearches = getLinkedInSearches(name);
      const contacts = getCompanyContacts(name);

      // Determine attendance type from confidence field
      const attendanceType = company.confidence === 'confirmed'
        ? 'Confirmed'
        : company.confidence === 'likely'
        ? 'Likely'
        : company.attendance_type || 'Unknown';

      companyMap.set(dedupeKey, {
        name,
        event: eventDiscovery.event_name,
        attendanceType,
        score: scoring?.icp_qualification?.weighted_score || 0,
        qualificationSummary: scoring?.qualification_summary || '',
        scoring,
        targetRoles,
        linkedInSearches,
        contacts,
      });
    }
  }

  // Sort by score (highest first)
  return Array.from(companyMap.values()).sort((a, b) => b.score - a.score);
}

// Get all outreach messages (reads from companies/{co}/roles/)
export function getAllOutreach(): ContactWithOutreach[] {
  const companyFolders = getCompanyFolders();
  const allContacts: ContactWithOutreach[] = [];

  for (const companyFolder of companyFolders) {
    const contacts = getCompanyContacts(companyFolder);
    allContacts.push(...contacts);
  }

  return allContacts;
}

// Get enriched events with scoring and company data
export function getEnrichedEvents() {
  const scoredEvents = getScoredEvents();
  const discoveredEvents = getDiscoveredEvents();
  const eventCompanies = getEventCompanies();

  console.log('[DATA] Processing events:', {
    discovered: discoveredEvents.length,
    scored: scoredEvents?.scored_events?.length || 0
  });

  const events = discoveredEvents.map((discoveredEvent) => {
    const scoreData = scoredEvents?.scored_events?.find(
      (scoredEvent) => scoredEvent.event_url === discoveredEvent.event_url
    );
    const companyData = eventCompanies.find(
      (ec) => ec.event_url === discoveredEvent.event_url
    );

    // Debug Summer Fancy Food Show
    if (discoveredEvent.event_name?.includes('Summer Fancy Food Show')) {
      console.log('[DATA] Summer Fancy Food Show:', {
        discoveredName: discoveredEvent.event_name,
        discoveredURL: discoveredEvent.event_url,
        foundScoreData: !!scoreData,
        scoreDataName: scoreData?.event_name,
        scoreDataScore: scoreData?.overall_score
      });
    }

    return {
      ...discoveredEvent,
      ...scoreData,
      companies: companyData?.companies || [],
      totalConfirmed: companyData?.total_confirmed || 0,
      totalLikely: companyData?.total_likely || 0,
    };
  });

  return events;
}

// Get dashboard stats
export function getDashboardStats() {
  const scoredEvents = getScoredEvents();
  const companies = getAllCompaniesWithDetails();
  const allOutreach = getAllOutreach();

  const totalEvents = scoredEvents?.scored_events?.length || 0;
  const totalCompanies = companies.length;
  const totalContacts = companies.reduce((sum, c) => sum + c.contacts.length, 0);
  const totalMessages = allOutreach.filter(c => c.outreach).length;

  return {
    events: totalEvents,
    companies: totalCompanies,
    contacts: totalContacts,
    messages: totalMessages,
  };
}

// Get unique events for filter dropdown
export function getUniqueEvents(): string[] {
  const companies = getAllCompaniesWithDetails();
  const events = new Set(companies.map(c => c.event).filter(Boolean));
  return Array.from(events).sort();
}
