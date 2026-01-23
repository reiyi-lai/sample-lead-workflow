"use client";

import { useState } from "react";
import { Company } from "@/lib/data";

interface EventWithCompanies {
  event_name: string;
  event_url?: string;
  dates?: string;
  location?: string;
  tier?: number;
  companies: Company[];
  totalConfirmed: number;
  totalLikely: number;
}

interface EventsListProps {
  events: EventWithCompanies[];
}

export default function EventsList({ events }: EventsListProps) {
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [tierFilter, setTierFilter] = useState("all");

  const filteredEvents = events.filter((event) => {
    if (tierFilter === "all") return true;
    return event.tier === parseInt(tierFilter);
  });

  const tierColors: Record<number, string> = {
    1: "bg-green-100 text-green-800",
    2: "bg-yellow-100 text-yellow-800",
    3: "bg-gray-100 text-gray-800",
  };

  return (
    <div>
      {/* Filter */}
      <div className="flex items-center justify-end mb-6">
        <select
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
        >
          <option value="all">All Tiers</option>
          <option value="1">Tier 1</option>
          <option value="2">Tier 2</option>
          <option value="3">Tier 3</option>
        </select>
      </div>

      {/* Events */}
      <div className="space-y-4">
        {filteredEvents.map((event) => {
          const isExpanded = expandedEvent === event.event_name;

          return (
            <div
              key={event.event_name}
              className="bg-white rounded-xl border border-gray-200 overflow-hidden"
            >
              {/* Event Header */}
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() =>
                  setExpandedEvent(isExpanded ? null : event.event_name)
                }
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {event.tier && (
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          tierColors[event.tier] || tierColors[3]
                        }`}
                      >
                        Tier {event.tier}
                      </span>
                    )}
                    <h3 className="font-semibold text-gray-900">
                      {event.event_name}
                    </h3>
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">
                    {isExpanded ? "▲" : "▼"}
                  </button>
                </div>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  {event.dates && <span>{event.dates}</span>}
                  {event.location && <span>• {event.location}</span>}
                  <span>• {event.companies.length} companies</span>
                </div>
              </div>

              {/* Expanded Company List */}
              {isExpanded && event.companies.length > 0 && (
                <div className="border-t border-gray-200">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                          Company
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                          Contacts
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {event.companies.map((company, index) => {
                        // Derive attendance type from source or confidence fields
                        const attendanceType = company.source?.includes('confirmed')
                          ? 'Confirmed'
                          : company.confidence === 'likely'
                          ? 'Likely'
                          : company.attendance_type || 'Unknown';

                        return (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {company.company_name}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              <span
                                className={`px-2 py-1 rounded-full text-xs ${
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
                            <td className="px-4 py-3 text-sm text-gray-500">
                              —
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {isExpanded && event.companies.length === 0 && (
                <div className="border-t border-gray-200 p-6 text-center text-gray-500">
                  No companies discovered for this event yet.
                </div>
              )}
            </div>
          );
        })}

        {filteredEvents.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No events found matching your filter.
          </div>
        )}
      </div>
    </div>
  );
}
