"use client";

import { useState, useMemo } from "react";
import { Company, EventScores } from "@/lib/data";
import EventsFilters from "./EventsFilters";
import { isEventInDateRange } from "@/lib/dateUtils";

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

  // Get available industries for filter dropdown
  const availableIndustries = useMemo(() => {
    const industries = new Set(
      events
        .map(event => event.industry_vertical)
        .filter(Boolean)
        .filter((industry): industry is string => typeof industry === 'string')
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

    // Apply industry filter
    if (selectedIndustry) {
      filtered = filtered.filter(event => event.industry_vertical === selectedIndustry);
    }

    // Sort events
    return filtered.sort((a, b) => {
      if (sortBy === "score") {
        return (b.overall_score || 0) - (a.overall_score || 0);
      } else if (sortBy === "date") {
        // Sort by date (upcoming first)
        if (!a.dates && !b.dates) return 0;
        if (!a.dates) return 1;
        if (!b.dates) return -1;

        // Parse dates more carefully - handle "February 2-4, 2026" format
        const parseDateString = (dateStr: string) => {
          // Handle formats like "February 2-4, 2026" or "March 1-4, 2026"
          const parts = dateStr.split(', ');
          if (parts.length === 2) {
            const year = parts[1];
            const monthDay = parts[0];
            const monthMatch = monthDay.match(/^(\w+)\s+(\d+)/);
            if (monthMatch) {
              const month = monthMatch[1];
              const day = monthMatch[2];
              return new Date(`${month} ${day}, ${year}`);
            }
          }
          // Fallback to original parsing
          return new Date(dateStr.split(' - ')[0] || dateStr);
        };

        const dateA = parseDateString(a.dates);
        const dateB = parseDateString(b.dates);
        return dateA.getTime() - dateB.getTime();
      }
      return 0;
    });
  }, [events, dateRange, selectedIndustry, sortBy]);

  const getIndustryBadgeColor = (industry?: string) => {
    switch (industry) {
      case "distribution": return "bg-blue-100 text-blue-800";
      case "construction_supply": return "bg-orange-100 text-orange-800";
      case "industrial_parts": return "bg-gray-100 text-gray-800";
      case "field_service": return "bg-purple-100 text-purple-800";
      case "pool_spa": return "bg-cyan-100 text-cyan-800";
      case "others": return "bg-green-100 text-green-800";
      default: return "bg-gray-100 text-gray-600";
    }
  };

  const formatIndustryLabel = (industry?: string) => {
    if (!industry) return "General";
    if (industry === "others") return "Others";
    return industry.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
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

    const scoreCategories = [
      { key: "industry_alignment", label: "Industry Alignment", weight: "45%" },
      { key: "scale_timing", label: "Scale & Timing", weight: "25%" },
      { key: "buyer_quality", label: "Buyer Quality", weight: "20%" },
      { key: "buyer_intent_alignment", label: "Buyer Intent", weight: "10%" },
    ];

    return (
      <div className="space-y-4">
        {scoreCategories.map(({ key, label, weight }) => {
          const scoreData = scores[key as keyof EventScores];
          if (!scoreData) return null;

          const score = scoreData.score;
          const getScoreColor = (s: number) => {
            if (s >= 8) return "text-green-600 bg-green-50 border-green-200";
            if (s >= 6) return "text-yellow-600 bg-yellow-50 border-yellow-200";
            return "text-red-600 bg-red-50 border-red-200";
          };

          return (
            <div key={key} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{label}</h4>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">{weight}</span>
                  <span className={`px-2 py-1 rounded text-sm font-medium border ${getScoreColor(score)}`}>
                    {score}/10
                  </span>
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
      </div>

      {/* Results Summary */}
      {(dateRange || selectedIndustry) && (
        <div className="mb-4 text-sm text-gray-600">
          Showing {filteredAndSortedEvents.length} of {events.length} events
        </div>
      )}

      <div className="space-y-4">
        {filteredAndSortedEvents.map((event) => {
          const isExpanded = expandedEvent === event.event_name;

          return (
            <div
              key={event.event_name}
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
                  <button className="ml-4 text-gray-400 hover:text-gray-600 transition-colors">
                    {isExpanded ? "▲" : "▼"}
                  </button>
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
    </div>
  );
}
