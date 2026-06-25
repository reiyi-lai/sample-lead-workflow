"use client";

import { useState, useMemo, useEffect } from "react";
import { Company, EventScores } from "@/lib/data";
import EventsFilters from "./EventsFilters";
import { isEventInDateRange, parseEventDate } from "@/lib/dateUtils";
import { getAttendance, updateAttendance, getFeedback, updateFeedback } from "@/lib/api";
import AddEventsModal from "./AddEventsForm";
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
  const [selectedScoringType, setSelectedScoringType] = useState<string | null>(null);
  const [attendingFilter, setAttendingFilter] = useState<boolean | null>(null);

  const [attendance, setAttendance] = useState<Record<string, { attending: boolean; whos_going: string }>>({});
  const [feedback, setFeedback] = useState<Record<string, { would_attend_again: boolean | null; notes: string }>>({});
  const [attendanceModal, setAttendanceModal] = useState<string | null>(null);
  const [feedbackModal, setFeedbackModal] = useState<string | null>(null);
  const [whosGoingDraft, setWhosGoingDraft] = useState("");
  const [feedbackDraft, setFeedbackDraft] = useState<{ would_attend_again: boolean | null; notes: string }>({ would_attend_again: null, notes: "" });

  useEffect(() => {
    getAttendance().then(setAttendance).catch(() => {});
    getFeedback().then(setFeedback).catch(() => {});
  }, []);

  const handleAttendingToggle = async (eventUrl: string) => {
    const current = attendance[eventUrl];
    const newAttending = !current?.attending;
    const whos = current?.whos_going || "";
    setAttendance((prev) => ({ ...prev, [eventUrl]: { attending: newAttending, whos_going: whos } }));
    await updateAttendance(eventUrl, newAttending, whos).catch(() => {});
  };

  const openAttendanceModal = (eventUrl: string) => {
    setWhosGoingDraft(attendance[eventUrl]?.whos_going || "");
    setAttendanceModal(eventUrl);
  };

  const saveAttendanceModal = async () => {
    if (!attendanceModal) return;
    const current = attendance[attendanceModal];
    setAttendance((prev) => ({ ...prev, [attendanceModal]: { attending: current?.attending ?? true, whos_going: whosGoingDraft } }));
    await updateAttendance(attendanceModal, current?.attending ?? true, whosGoingDraft).catch(() => {});
    setAttendanceModal(null);
  };

  const openFeedbackModal = (eventUrl: string) => {
    const existing = feedback[eventUrl];
    setFeedbackDraft({ would_attend_again: existing?.would_attend_again ?? true, notes: existing?.notes || "" });
    setFeedbackModal(eventUrl);
  };

  const saveFeedbackModal = async () => {
    if (!feedbackModal) return;
    setFeedback((prev) => ({ ...prev, [feedbackModal]: feedbackDraft }));
    await updateFeedback(feedbackModal, feedbackDraft.would_attend_again, feedbackDraft.notes).catch(() => {});
    setFeedbackModal(null);
  };

  const availableIndustries = useMemo(() => {
    const industries = new Set(
      events
        .map(event => {
          const raw = event.industry_vertical;
          if (!raw || typeof raw !== 'string') return null;
          return raw.split(",")[0].trim().toLowerCase().replace(/\s+/g, "_");
        })
        .filter((v): v is string => !!v)
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
      filtered = filtered.filter(event => {
        if (!event.industry_vertical) return false;
        const primary = event.industry_vertical.split(",")[0].trim().toLowerCase().replace(/\s+/g, "_");
        return primary === selectedIndustry;
      });
    }

    if (selectedScoringType) {
      filtered = filtered.filter(event => {
        const hasSupplyChain = event.scores && "supply_chain_vertical_alignment" in event.scores;
        return selectedScoringType === "supply_chain" ? hasSupplyChain : !hasSupplyChain;
      });
    }

    if (attendingFilter !== null) {
      filtered = filtered.filter(event => {
        const isAttending = attendance[event.event_url || ""]?.attending || false;
        return attendingFilter ? isAttending : !isAttending;
      });
    }

    return filtered.sort((a, b) => {
      if (sortBy === "score") {
        return (b.overall_score || 0) - (a.overall_score || 0);
      } else if (sortBy === "date") {
        const parsedA = a.dates ? parseEventDate(a.dates) : { start: null, end: null };
        const parsedB = b.dates ? parseEventDate(b.dates) : { start: null, end: null };

        if (!parsedA.start && !parsedB.start) return 0;
        if (!parsedA.start) return 1;
        if (!parsedB.start) return -1;

        const startDiff = parsedA.start.getTime() - parsedB.start.getTime();
        if (startDiff !== 0) return startDiff;

        const endA = (parsedA.end || parsedA.start).getTime();
        const endB = (parsedB.end || parsedB.start).getTime();
        return endA - endB;
      }
      return 0;
    });
  }, [events, dateRange, selectedIndustry, selectedScoringType, sortBy, attendingFilter, attendance]);

  const getPrimaryVertical = (industry?: string): string => {
    if (!industry) return "";
    return industry.split(",")[0].trim().toLowerCase().replace(/\s+/g, "_");
  };

  const getIndustryBadgeColor = (industry?: string) => {
    const primary = getPrimaryVertical(industry);
    if (primary.includes("distribution") || primary.includes("wholesale")) return "border-blue-300 text-blue-700 bg-blue-50";
    if (primary.includes("construction")) return "border-amber-300 text-amber-700 bg-amber-50";
    if (primary.includes("industrial")) return "border-slate-300 text-slate-700 bg-slate-50";
    if (primary.includes("field_service")) return "border-violet-300 text-violet-700 bg-violet-50";
    if (primary.includes("food")) return "border-emerald-300 text-emerald-700 bg-emerald-50";
    if (primary.includes("supply_chain") || primary.includes("supply_management") || primary.includes("procurement") || primary.includes("logistics")) return "border-indigo-300 text-indigo-700 bg-indigo-50";
    if (primary.includes("automotive") || primary.includes("automotives")) return "border-red-300 text-red-700 bg-red-50";
    if (primary.includes("pharmaceutic") || primary.includes("healthcare")) return "border-teal-300 text-teal-700 bg-teal-50";
    if (primary.includes("manufacturing")) return "border-amber-300 text-amber-700 bg-amber-50";
    if (primary.includes("fleet")) return "border-sky-300 text-sky-700 bg-sky-50";
    return "border-neutral-200 text-neutral-500 bg-neutral-50";
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return "bg-emerald-100 text-emerald-800";
    if (score >= 6) return "bg-amber-100 text-amber-800";
    return "bg-red-100 text-red-800";
  };

  const formatIndustryLabel = (industry?: string) => {
    if (!industry) return "General";
    const primary = industry.split(",")[0].trim();
    return primary.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
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

    const labelMap: Record<string, string> = {
      supply_chain_vertical_alignment: "Supply Chain Vertical Alignment",
      buyer_functional_alignment: "Buyer Functional Alignment",
      event_scale_timing: "Event Scale & Timing",
      buyer_seniority: "Buyer Seniority",
      industry_alignment: "Industry Alignment",
      scale_timing: "Scale & Timing",
      buyer_quality: "Buyer Quality",
      buyer_intent_alignment: "Buyer Intent",
    };

    const presentKeys = Object.keys(scores).filter(
      (key) => scores[key] && typeof scores[key] === "object" && "score" in scores[key]!
    );

    const hasSupplyChain = presentKeys.includes("supply_chain_vertical_alignment");

    const orderedKeys = hasSupplyChain
      ? [
          "supply_chain_vertical_alignment",
          ...presentKeys.filter((k) => k !== "supply_chain_vertical_alignment"),
        ]
      : presentKeys;

    return (
      <div className="space-y-3">
        {hasSupplyChain && (
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide border border-indigo-300 text-indigo-700 bg-indigo-50">
              Supply Chain Event
            </span>
          </div>
        )}
        {orderedKeys.map((key) => {
          const scoreData = scores[key];
          if (!scoreData) return null;

          const score = typeof scoreData.score === "number" ? scoreData.score : null;

          const label =
            labelMap[key] ||
            key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

          return (
            <div
              key={key}
              className={`border rounded-lg p-4 ${
                key === "supply_chain_vertical_alignment"
                  ? "border-indigo-200 bg-indigo-50/30"
                  : "border-neutral-200"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-neutral-950">{label}</h4>
                <div className="flex items-center gap-2">
                  {score !== null ? (
                    <span className={`px-2 py-0.5 rounded text-sm font-semibold ${getScoreColor(score)}`}>
                      {score}/10
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-sm font-medium border border-neutral-200 text-neutral-400 bg-neutral-50">
                      N/A
                    </span>
                  )}
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
        onScoringTypeChange={setSelectedScoringType}
        onAttendingFilterChange={setAttendingFilter}
        availableIndustries={availableIndustries}
      />

      <div className="flex items-center gap-3 py-2 mb-4">
        <span className="text-xs text-neutral-500 uppercase tracking-wide">Sort by</span>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "score" | "date")}
          className="px-3 py-1.5 border border-neutral-200 rounded-md text-sm text-neutral-900 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="score">Score</option>
          <option value="date">Date</option>
        </select>
        <div className="ml-auto">
          <AddEventsModal />
        </div>
      </div>

      {(dateRange || selectedIndustry || selectedScoringType || attendingFilter !== null) && (
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
                  <div className="flex items-center gap-3 ml-4">
                    <label className="flex items-center gap-2 cursor-pointer" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={attendance[event.event_url || ""]?.attending || false}
                        onChange={() => event.event_url && handleAttendingToggle(event.event_url)}
                        className="w-4 h-4 rounded border-neutral-300 text-neutral-950 accent-neutral-950"
                      />
                      <span className="text-xs text-neutral-500">Attending</span>
                    </label>
                    {attendance[event.event_url || ""]?.attending && (
                      <button
                        onClick={(e) => { e.stopPropagation(); event.event_url && openAttendanceModal(event.event_url); }}
                        className="text-xs text-neutral-500 hover:text-neutral-950 underline underline-offset-2"
                      >
                        Who&apos;s going?
                      </button>
                    )}
                    <button
                      onClick={(e) => { e.stopPropagation(); event.event_url && openFeedbackModal(event.event_url); }}
                      className="text-xs px-2.5 py-1 rounded-md border border-neutral-200 text-neutral-600 hover:bg-neutral-100 transition-colors"
                    >
                      Feedback
                    </button>
                    <span className="text-neutral-300 hover:text-neutral-600 transition-colors">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </span>
                  </div>
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
                            : "text-neutral-500 hover:text-neutral-700"
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
                            <h4 className="text-xs font-medium text-blue-700 mb-2 uppercase tracking-wide">Sales Brief</h4>
                            <p className="text-sm text-neutral-700 leading-relaxed">{event.sales_brief}</p>
                          </div>
                        )}

                        <div className="border border-neutral-200 rounded-lg p-4">
                          <h4 className="text-xs font-medium text-blue-700 mb-3 uppercase tracking-wide">Event Information</h4>
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

      {attendanceModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setAttendanceModal(null)}>
          <div className="bg-white rounded-lg border border-neutral-200 shadow-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-neutral-950 mb-4">Who&apos;s going?</h3>
            <textarea
              value={whosGoingDraft}
              onChange={(e) => setWhosGoingDraft(e.target.value)}
              placeholder="e.g. John, Sarah, Mike..."
              className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 h-24 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <div className="flex justify-end gap-3 mt-4">
              <button onClick={() => setAttendanceModal(null)} className="text-xs text-neutral-500 hover:text-neutral-700">Cancel</button>
              <button onClick={saveAttendanceModal} className="text-xs px-4 py-2 bg-neutral-950 text-white rounded-md hover:bg-neutral-800 transition-colors">Save</button>
            </div>
          </div>
        </div>
      )}

      {feedbackModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setFeedbackModal(null)}>
          <div className="bg-white rounded-lg border border-neutral-200 shadow-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-neutral-950 mb-4">Post-Event Feedback</h3>
            <div className="mb-4">
              <label className="block text-[10px] font-medium text-neutral-500 mb-2 uppercase tracking-wide">Would attend in future?</label>
              <div className="flex gap-2">
                {([true, false, null] as const).map((val) => (
                  <button
                    key={String(val)}
                    onClick={() => setFeedbackDraft((d) => ({ ...d, would_attend_again: val }))}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
                      feedbackDraft.would_attend_again === val
                        ? val === true ? "bg-emerald-100 border-emerald-300 text-emerald-800" : val === false ? "bg-red-100 border-red-300 text-red-800" : "bg-neutral-200 border-neutral-300 text-neutral-800"
                        : "border-neutral-200 text-neutral-600 hover:bg-neutral-50"
                    }`}
                  >
                    {val === true ? "Yes" : val === false ? "No" : "Depends"}
                  </button>
                ))}
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-[10px] font-medium text-neutral-500 mb-2 uppercase tracking-wide">Notes</label>
              <textarea
                value={feedbackDraft.notes}
                onChange={(e) => setFeedbackDraft((d) => ({ ...d, notes: e.target.value }))}
                placeholder="How was the event? Any takeaways?"
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 h-24 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setFeedbackModal(null)} className="text-xs text-neutral-500 hover:text-neutral-700">Cancel</button>
              <button onClick={saveFeedbackModal} className="text-xs px-4 py-2 bg-neutral-950 text-white rounded-md hover:bg-neutral-800 transition-colors">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
