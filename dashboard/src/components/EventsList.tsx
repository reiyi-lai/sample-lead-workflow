"use client";

import { useState, useMemo } from "react";
import { Company, EventScores } from "@/lib/data";
import EventsFilters from "./EventsFilters";
import { isEventInDateRange } from "@/lib/dateUtils";
import { ChevronUp, ChevronDown, ExternalLink } from "lucide-react";

interface EventWithCompanies {
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
  companies: Company[];
  totalConfirmed: number;
  totalLikely: number;
}

interface EventsListProps {
  events: EventWithCompanies[];
}

interface DateRange {
  start: string;
  end: string;
}

export default function EventsList({ events }: EventsListProps) {
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"details" | "scoring" | "companies">("details");
  const [dateRange, setDateRange] = useState<DateRange | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"score" | "date">("score");

  const availableIndustries = useMemo(() => {
    const industries = new Set(
      events
        .map(event => event.industry_vertical)
        .filter(Boolean)
        .filter((industry): industry is string => typeof industry === 'string')
    );
    return Array.from(industries).sort();
  }, [events]);

  const filteredAndSortedEvents = useMemo(() => {
    let filtered = [...events];

    if (dateRange && dateRange.start && dateRange.end) {
      filtered = filtered.filter(event => {
        if (!event.dates) return false;
        return isEventInDateRange(event.dates, dateRange.start, dateRange.end);
      });
    }

    if (selectedIndustry) {
      filtered = filtered.filter(event => event.industry_vertical === selectedIndustry);
    }

    return filtered.sort((a, b) => {
      if (sortBy === "score") {
        return (b.overall_score || 0) - (a.overall_score || 0);
      } else if (sortBy === "date") {
        if (!a.dates && !b.dates) return 0;
        if (!a.dates) return 1;
        if (!b.dates) return -1;

        const parseDateString = (dateStr: string) => {
          const parts = dateStr.split(', ');
          if (parts.length === 2) {
            const year = parts[1];
            const monthDay = parts[0];
            const monthMatch = monthDay.match(/^(\w+)\s+(\d+)/);
            if (monthMatch) {
              return new Date(`${monthMatch[1]} ${monthMatch[2]}, ${year}`);
            }
          }
          return new Date(dateStr.split(' - ')[0] || dateStr);
        };

        return parseDateString(a.dates).getTime() - parseDateString(b.dates).getTime();
      }
      return 0;
    });
  }, [events, dateRange, selectedIndustry, sortBy]);

  const formatIndustryLabel = (industry?: string) => {
    if (!industry) return "General";
    if (industry === "others") return "Others";
    return industry.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  };

  const getIndustryBadgeColor = (industry?: string) => {
    switch (industry) {
      case "distribution": return "border-blue-300 text-blue-700 bg-blue-50";
      case "construction_supply": return "border-amber-300 text-amber-700 bg-amber-50";
      case "industrial_parts": return "border-slate-300 text-slate-700 bg-slate-50";
      case "field_service": return "border-violet-300 text-violet-700 bg-violet-50";
      case "pool_spa": return "border-cyan-300 text-cyan-700 bg-cyan-50";
      case "others": return "border-emerald-300 text-emerald-700 bg-emerald-50";
      default: return "border-neutral-200 text-neutral-500 bg-neutral-50";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return "bg-emerald-100 text-emerald-800";
    if (score >= 6) return "bg-amber-100 text-amber-800";
    return "bg-red-100 text-red-800";
  };

  const renderScoringBreakdown = (scores?: EventScores) => {
    if (!scores) {
      return (
        <div className="text-center py-8 text-neutral-500">
          <p>Scoring breakdown not available yet.</p>
          <p className="text-sm mt-1">Run the event scoring pipeline to see detailed scores.</p>
        </div>
      );
    }

    const scoreCategories = [
      { key: "industry_alignment", label: "Industry Alignment", weight: "45%" },
      { key: "scale_timing", label: "Scale & Timing", weight: "25%" },
      { key: "buyer_quality", label: "Buyer Quality", weight: "20%" },
      { key: "buyer_intent_alignment", label: "Buyer Intent", weight: "10%" },
    ];

    return (
      <div className="space-y-3">
        {scoreCategories.map(({ key, label, weight }) => {
          const scoreData = scores[key as keyof EventScores];
          if (!scoreData) return null;

          const score = scoreData.score;

          return (
            <div key={key} className="border border-neutral-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-neutral-950">{label}</h4>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wide">{weight}</span>
                  <span className={`px-2 py-0.5 rounded text-sm font-semibold ${getScoreColor(score)}`}>
                    {score}/10
                  </span>
                </div>
              </div>
              <p className="text-sm text-neutral-500 leading-relaxed">{scoreData.rationale}</p>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div>
      <EventsFilters
        onDateRangeChange={setDateRange}
        onIndustryChange={setSelectedIndustry}
        availableIndustries={availableIndustries}
      />

      <div className="flex items-center gap-3 py-2 mb-4">
        <span className="text-xs text-neutral-500 uppercase tracking-wide">Sort by</span>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "score" | "date")}
          className="px-3 py-1.5 border border-neutral-200 rounded-md text-sm text-neutral-900 bg-white focus:outline-none focus:ring-1 focus:ring-neutral-500"
        >
          <option value="score">Score</option>
          <option value="date">Date</option>
        </select>
      </div>

      {(dateRange || selectedIndustry) && (
        <div className="mb-4 text-xs text-neutral-500">
          {filteredAndSortedEvents.length} of {events.length} events
        </div>
      )}

      <div className="space-y-3">
        {filteredAndSortedEvents.map((event) => {
          const isExpanded = expandedEvent === event.event_name;

          return (
            <div
              key={event.event_url}
              className="border border-neutral-200 rounded-2xl overflow-hidden"
            >
              <div
                className="p-5 cursor-pointer hover:bg-neutral-50 transition-colors"
                onClick={() => {
                  setExpandedEvent(isExpanded ? null : event.event_name);
                  if (!isExpanded) setActiveTab("details");
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2.5 mb-2">
                      {event.overall_score != null && (
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getScoreColor(event.overall_score)}`}>
                          {event.overall_score.toFixed(1)}
                        </span>
                      )}
                      {event.industry_vertical && (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide border ${getIndustryBadgeColor(event.industry_vertical)}`}>
                          {formatIndustryLabel(event.industry_vertical)}
                        </span>
                      )}
                    </div>
                    <h3 className="text-base font-semibold text-neutral-950 mb-1.5">
                      {event.event_name}
                    </h3>
                    <div className="flex items-center gap-4 text-xs text-neutral-500">
                      {event.dates && <span>{event.dates}</span>}
                      <span>{event.companies.length} companies</span>
                    </div>
                  </div>
                  <button className="ml-4 text-neutral-300 hover:text-neutral-600 transition-colors">
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="border-t border-neutral-200">
                  <div className="flex border-b border-neutral-200">
                    {(["details", "scoring", "companies"] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-5 py-2.5 text-xs font-medium uppercase tracking-wide transition-colors ${
                          activeTab === tab
                            ? "text-neutral-950 border-b-2 border-neutral-950"
                            : "text-neutral-500 hover:text-neutral-600"
                        }`}
                      >
                        {tab === "companies" ? `Companies (${event.companies.length})` : tab === "details" ? "Details" : "Scoring"}
                      </button>
                    ))}
                  </div>

                  <div className="p-5">
                    {activeTab === "details" && (
                      <div className="space-y-5">
                        {event.sales_brief && (
                          <div className="border border-neutral-200 rounded-lg p-4">
                            <h4 className="text-xs font-medium text-neutral-500 mb-2 uppercase tracking-wide">Sales Brief</h4>
                            <p className="text-sm text-neutral-700 leading-relaxed">{event.sales_brief}</p>
                          </div>
                        )}

                        <div>
                          <h4 className="text-xs font-medium text-neutral-500 mb-3 uppercase tracking-wide">Event Information</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {event.dates && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Dates</span>
                                <p className="text-sm text-neutral-900 mt-0.5">{event.dates}</p>
                              </div>
                            )}
                            {event.location && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Location</span>
                                <p className="text-sm text-neutral-900 mt-0.5">{event.location}</p>
                              </div>
                            )}
                            {event.venue && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Venue</span>
                                <p className="text-sm text-neutral-900 mt-0.5">{event.venue}</p>
                              </div>
                            )}
                            {event.cost && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Cost</span>
                                <p className="text-sm text-neutral-900 mt-0.5">{event.cost}</p>
                              </div>
                            )}
                            {event.event_url && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Website</span>
                                <br />
                                <a
                                  href={event.event_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm text-neutral-900 hover:text-neutral-600 underline underline-offset-2 break-all inline-flex items-center gap-1"
                                >
                                  {event.event_url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
                                  <ExternalLink size={12} />
                                </a>
                              </div>
                            )}
                            {event.industry_vertical && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Industry</span>
                                <p className="text-sm text-neutral-900 mt-0.5">{formatIndustryLabel(event.industry_vertical)}</p>
                              </div>
                            )}
                            {event.description && (
                              <div className="col-span-full">
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Description</span>
                                <p className="text-sm text-neutral-700 leading-relaxed mt-0.5">{event.description}</p>
                              </div>
                            )}
                            {event.exhibitor_mix && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Exhibitor Mix</span>
                                <p className="text-sm text-neutral-900 mt-0.5">{event.exhibitor_mix}</p>
                              </div>
                            )}
                            {event.audience_mix && (
                              <div>
                                <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Audience Mix</span>
                                <p className="text-sm text-neutral-900 mt-0.5">{event.audience_mix}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {activeTab === "scoring" && renderScoringBreakdown(event.scores)}

                    {activeTab === "companies" && (
                      <div>
                        {event.companies.length > 0 ? (
                          <table className="w-full">
                            <thead>
                              <tr className="border-b border-neutral-200">
                                <th className="text-left py-2.5 text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Company</th>
                                <th className="text-left py-2.5 text-[10px] font-medium text-neutral-500 uppercase tracking-wide">Type</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-neutral-100">
                              {event.companies.map((company, index) => {
                                const attendanceType = company.confidence === 'confirmed'
                                  ? 'Confirmed'
                                  : company.confidence === 'likely'
                                  ? 'Likely'
                                  : company.attendance_type || 'Unknown';

                                return (
                                  <tr key={index} className="hover:bg-neutral-50">
                                    <td className="py-2.5 text-sm text-neutral-900">
                                      {company.company_name}
                                    </td>
                                    <td className="py-2.5">
                                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wide ${
                                        attendanceType === "Confirmed"
                                          ? "bg-emerald-100 text-emerald-700"
                                          : attendanceType === "Likely"
                                          ? "bg-blue-100 text-blue-700"
                                          : "bg-neutral-100 text-neutral-500"
                                      }`}>
                                        {attendanceType}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        ) : (
                          <div className="text-center py-8 text-neutral-500 text-sm">
                            No companies discovered for this event yet.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filteredAndSortedEvents.length === 0 && (
          <div className="text-center py-12 text-neutral-500 text-sm">
            {events.length === 0
              ? "No events found."
              : "No events match the selected filters."
            }
          </div>
        )}
      </div>
    </div>
  );
}
