"use client";

import { useState, useMemo, useEffect } from "react";
import { Company, EventScores } from "@/lib/data";
import EventsFilters from "./EventsFilters";
import { isEventInDateRange, parseEventDate } from "@/lib/dateUtils";
import { getAttendance, updateAttendance, getFeedback, updateFeedback } from "@/lib/api";
import AddEventsModal from "./AddEventsForm";

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

  // Get available industries for filter dropdown (grouped by primary vertical)
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

  // Filter and sort events
  const filteredAndSortedEvents = useMemo(() => {
    let filtered = [...events];

    // Apply date range filter
    if (dateRange && dateRange.start && dateRange.end) {
      filtered = filtered.filter(event => {
        if (!event.dates) return false;
        return isEventInDateRange(event.dates, dateRange.start, dateRange.end);
      });
    }

    // Apply industry filter (match on primary vertical)
    if (selectedIndustry) {
      filtered = filtered.filter(event => {
        if (!event.industry_vertical) return false;
        const primary = event.industry_vertical.split(",")[0].trim().toLowerCase().replace(/\s+/g, "_");
        return primary === selectedIndustry;
      });
    }

    // Apply scoring type filter
    if (selectedScoringType) {
      filtered = filtered.filter(event => {
        const hasSupplyChain = event.scores && "supply_chain_vertical_alignment" in event.scores;
        return selectedScoringType === "supply_chain" ? hasSupplyChain : !hasSupplyChain;
      });
    }

    // Apply attending filter
    if (attendingFilter !== null) {
      filtered = filtered.filter(event => {
        const isAttending = attendance[event.event_url || ""]?.attending || false;
        return attendingFilter ? isAttending : !isAttending;
      });
    }

    // Sort events
    return filtered.sort((a, b) => {
      if (sortBy === "score") {
        return (b.overall_score || 0) - (a.overall_score || 0);
      } else if (sortBy === "date") {
        // Sort by start date (upcoming first)
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
    if (primary.includes("distribution") || primary.includes("wholesale")) return "bg-blue-100 text-blue-800";
    if (primary.includes("construction")) return "bg-orange-100 text-orange-800";
    if (primary.includes("industrial")) return "bg-gray-100 text-gray-800";
    if (primary.includes("field_service")) return "bg-purple-100 text-purple-800";
    if (primary.includes("food")) return "bg-emerald-100 text-emerald-800";
    if (primary.includes("supply_chain") || primary.includes("supply_management") || primary.includes("procurement") || primary.includes("logistics")) return "bg-indigo-100 text-indigo-800";
    if (primary.includes("automotive") || primary.includes("automotives")) return "bg-red-100 text-red-800";
    if (primary.includes("pharmaceutic") || primary.includes("healthcare")) return "bg-teal-100 text-teal-800";
    if (primary.includes("manufacturing")) return "bg-amber-100 text-amber-800";
    if (primary.includes("fleet")) return "bg-sky-100 text-sky-800";
    return "bg-gray-100 text-gray-600";
  };

  const formatIndustryLabel = (industry?: string) => {
    if (!industry) return "General";
    const primary = industry.split(",")[0].trim();
    return primary.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  };

  const renderScoringBreakdown = (scores?: EventScores) => {
    if (!scores) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>Scoring breakdown not available yet.</p>
          <p className="text-sm">Run the event scoring pipeline to see detailed scores and rationales.</p>
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
      <div className="space-y-4">
        {hasSupplyChain && (
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-1 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
              Supply Chain Event
            </span>
          </div>
        )}
        {orderedKeys.map((key) => {
          const scoreData = scores[key];
          if (!scoreData) return null;

          const score = typeof scoreData.score === "number" ? scoreData.score : null;
          const getScoreColor = (s: number) => {
            if (s >= 8) return "text-green-600 bg-green-50 border-green-200";
            if (s >= 6) return "text-yellow-600 bg-yellow-50 border-yellow-200";
            return "text-red-600 bg-red-50 border-red-200";
          };

          const label =
            labelMap[key] ||
            key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

          return (
            <div
              key={key}
              className={`border rounded-lg p-4 ${
                key === "supply_chain_vertical_alignment"
                  ? "border-indigo-200 bg-indigo-50/30"
                  : "border-gray-200"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{label}</h4>
                <div className="flex items-center gap-2">
                  {score !== null ? (
                    <span
                      className={`px-2 py-1 rounded text-sm font-medium border ${getScoreColor(score)}`}
                    >
                      {score}/10
                    </span>
                  ) : (
                    <span className="px-2 py-1 rounded text-sm font-medium border border-gray-200 text-gray-500 bg-gray-50">
                      N/A
                    </span>
                  )}
                </div>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{scoreData.rationale}</p>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div>
      {/* Filters */}
      <EventsFilters
        onDateRangeChange={setDateRange}
        onIndustryChange={setSelectedIndustry}
        onScoringTypeChange={setSelectedScoringType}
        onAttendingFilterChange={setAttendingFilter}
        availableIndustries={availableIndustries}
      />

      {/* Sort Section */}
      <div className="flex items-center gap-3 py-2 mb-4">
        <h3 className="font-semibold text-lg text-white">Sort:</h3>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "score" | "date")}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-900 bg-white"
        >
          <option value="score">Score (High to Low)</option>
          <option value="date">Date (Upcoming First)</option>
        </select>
        <div className="ml-auto">
          <AddEventsModal />
        </div>
      </div>

      {/* Results Summary */}
      {(dateRange || selectedIndustry || selectedScoringType || attendingFilter !== null) && (
        <div className="mb-4 text-sm text-gray-600">
          Showing {filteredAndSortedEvents.length} of {events.length} events
        </div>
      )}

      <div className="space-y-4">
        {filteredAndSortedEvents.map((event) => {
          const isExpanded = expandedEvent === event.event_name;

          return (
            <div
              key={event.event_url}
              className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
            >
              {/* Enhanced Event Header */}
              <div
                className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => {
                  setExpandedEvent(isExpanded ? null : event.event_name);
                  if (!isExpanded) setActiveTab("details");
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      {event.overall_score != null && (
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            event.overall_score >= 8
                              ? "bg-green-100 text-green-800"
                              : event.overall_score >= 6
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {event.overall_score.toFixed(1)}
                        </span>
                      )}
                      {event.industry_vertical && (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getIndustryBadgeColor(event.industry_vertical)}`}>
                          {formatIndustryLabel(event.industry_vertical)}
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {event.event_name}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      {event.dates && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-400">📅</span>
                          <span>{event.dates}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400">🏢</span>
                        <span>{event.companies.length} companies</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-4">
                    <label className="flex items-center gap-2 cursor-pointer" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={attendance[event.event_url || ""]?.attending || false}
                        onChange={() => event.event_url && handleAttendingToggle(event.event_url)}
                        className="w-4 h-4 rounded border-gray-300 text-blue-600"
                      />
                      <span className="text-xs text-gray-500">Attending</span>
                    </label>
                    {attendance[event.event_url || ""]?.attending && (
                      <button
                        onClick={(e) => { e.stopPropagation(); event.event_url && openAttendanceModal(event.event_url); }}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        Who&apos;s going?
                      </button>
                    )}
                    <button
                      onClick={(e) => { e.stopPropagation(); event.event_url && openFeedbackModal(event.event_url); }}
                      className="text-xs px-2 py-1 rounded border border-gray-300 text-gray-600 hover:bg-gray-100"
                    >
                      Feedback
                    </button>
                    <span className="text-gray-400 hover:text-gray-600 transition-colors">
                      {isExpanded ? "▲" : "▼"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="border-t border-gray-200">
                  {/* Tab Navigation */}
                  <div className="flex border-b border-gray-200 bg-gray-50">
                    <button
                      onClick={() => setActiveTab("details")}
                      className={`px-6 py-3 text-sm font-medium transition-colors ${
                        activeTab === "details"
                          ? "bg-white text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-600 hover:text-gray-800"
                      }`}
                    >
                      Event Details
                    </button>
                    <button
                      onClick={() => setActiveTab("scoring")}
                      className={`px-6 py-3 text-sm font-medium transition-colors ${
                        activeTab === "scoring"
                          ? "bg-white text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-600 hover:text-gray-800"
                      }`}
                    >
                      Scoring Breakdown
                    </button>
                    <button
                      onClick={() => setActiveTab("companies")}
                      className={`px-6 py-3 text-sm font-medium transition-colors ${
                        activeTab === "companies"
                          ? "bg-white text-blue-600 border-b-2 border-blue-600"
                          : "text-gray-600 hover:text-gray-800"
                      }`}
                    >
                      Companies ({event.companies.length})
                    </button>
                  </div>

                  {/* Tab Content */}
                  <div className="p-6">
                    {activeTab === "details" && (
                      <div className="space-y-6">
                        {/* Sales Brief */}
                        {event.sales_brief && (
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 className="font-medium text-blue-900 mb-3 flex items-center">
                              <span className="mr-2">🎯</span>
                              Sales Brief
                            </h4>
                            <p className="text-blue-800 leading-relaxed">{event.sales_brief}</p>
                          </div>
                        )}

                        {/* All Event Information */}
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="font-medium text-gray-900 mb-4">Event Information</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {event.dates && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Dates</span>
                                <p className="text-gray-900">{event.dates}</p>
                              </div>
                            )}
                            {event.location && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Location</span>
                                <p className="text-gray-900">{event.location}</p>
                              </div>
                            )}
                            {event.venue && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Venue</span>
                                <p className="text-gray-900">{event.venue}</p>
                              </div>
                            )}
                            {event.cost && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Cost</span>
                                <p className="text-gray-900">{event.cost}</p>
                              </div>
                            )}
                            {event.event_url && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Website</span>
                                <br />
                                <a
                                  href={event.event_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-800 underline break-all"
                                >
                                  {event.event_url}
                                </a>
                              </div>
                            )}
                            {event.industry_vertical && (
                              <div>
                                <span className="text-sm font-medium text-gray-500">Industry</span>
                                <p className="text-gray-900">{formatIndustryLabel(event.industry_vertical)}</p>
                              </div>
                            )}
                            {event.description && (
                              <div className="col-span-full">
                                <span className="text-sm font-medium text-gray-500">Description</span>
                                <p className="text-gray-900 leading-relaxed">{event.description}</p>
                              </div>
                            )}
                            {event.exhibitor_mix && (
                              <div className="col-span-full md:col-span-1">
                                <span className="text-sm font-medium text-gray-500">Exhibitor Mix</span>
                                <p className="text-gray-900">{event.exhibitor_mix}</p>
                              </div>
                            )}
                            {event.audience_mix && (
                              <div className="col-span-full md:col-span-1">
                                <span className="text-sm font-medium text-gray-500">Audience Mix</span>
                                <p className="text-gray-900">{event.audience_mix}</p>
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
                              <tr className="border-b border-gray-200">
                                <th className="text-left py-3 text-sm font-medium text-gray-500">Company</th>
                                <th className="text-left py-3 text-sm font-medium text-gray-500">Type</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {event.companies.map((company, index) => {
                                const attendanceType = company.confidence === 'confirmed'
                                  ? 'Confirmed'
                                  : company.confidence === 'likely'
                                  ? 'Likely'
                                  : company.attendance_type || 'Unknown';

                                return (
                                  <tr key={index} className="hover:bg-gray-50">
                                    <td className="py-3 text-sm text-gray-900">
                                      {company.company_name}
                                    </td>
                                    <td className="py-3">
                                      <span
                                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                                          attendanceType === "Confirmed"
                                            ? "bg-green-100 text-green-700"
                                            : attendanceType === "Likely"
                                            ? "bg-blue-100 text-blue-700"
                                            : "bg-gray-100 text-gray-600"
                                        }`}
                                      >
                                        {attendanceType}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
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
          <div className="text-center py-12 text-gray-500">
            {events.length === 0
              ? "No events found."
              : "No events match the selected filters."
            }
          </div>
        )}
      </div>

      {attendanceModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setAttendanceModal(null)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-gray-900 mb-4">Who&apos;s going?</h3>
            <textarea
              value={whosGoingDraft}
              onChange={(e) => setWhosGoingDraft(e.target.value)}
              placeholder="e.g. John, Sarah, Mike..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 h-24 resize-none"
            />
            <div className="flex justify-end gap-3 mt-4">
              <button onClick={() => setAttendanceModal(null)} className="text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button onClick={saveAttendanceModal} className="text-sm px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
            </div>
          </div>
        </div>
      )}

      {feedbackModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setFeedbackModal(null)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-gray-900 mb-4">Post-Event Feedback</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Would attend in future?</label>
              <div className="flex gap-3">
                {([true, false, null] as const).map((val) => (
                  <button
                    key={String(val)}
                    onClick={() => setFeedbackDraft((d) => ({ ...d, would_attend_again: val }))}
                    className={`px-3 py-1 rounded-md text-sm border ${
                      feedbackDraft.would_attend_again === val
                        ? val === true ? "bg-green-100 border-green-400 text-green-800" : val === false ? "bg-red-100 border-red-400 text-red-800" : "bg-gray-200 border-gray-400 text-gray-800"
                        : "border-gray-300 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    {val === true ? "Yes" : val === false ? "No" : "It depends"}
                  </button>
                ))}
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
              <textarea
                value={feedbackDraft.notes}
                onChange={(e) => setFeedbackDraft((d) => ({ ...d, notes: e.target.value }))}
                placeholder="How was the event? Any takeaways?"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 h-24 resize-none"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setFeedbackModal(null)} className="text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button onClick={saveFeedbackModal} className="text-sm px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
