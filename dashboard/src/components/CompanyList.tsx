"use client";

import { useState } from "react";
import { CompanyWithDetails } from "@/lib/data";
import CompanyCard from "./CompanyCard";

interface CompanyListProps {
  companies: CompanyWithDetails[];
  events: string[];
}

export default function CompanyList({ companies, events }: CompanyListProps) {
  const [search, setSearch] = useState("");
  const [eventFilter, setEventFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");

  // Filter companies
  const filteredCompanies = companies.filter((company) => {
    // Search filter
    if (search && !company.name.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }

    // Event filter
    if (eventFilter !== "all" && company.event !== eventFilter) {
      return false;
    }

    // Score filter
    if (scoreFilter === "high" && company.score < 80) return false;
    if (scoreFilter === "mid" && (company.score < 50 || company.score >= 80)) return false;
    if (scoreFilter === "low" && company.score >= 50) return false;

    return true;
  });

  return (
    <div>
      {/* Header with filters */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Companies</h2>

        <div className="flex items-center gap-4">
          {/* Search */}
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          {/* Event Filter */}
          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
            className="px-2 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
          >
            <option value="all">All Events</option>
            {events.map((event) => (
              <option key={event} value={event}>
                {event}
              </option>
            ))}
          </select>

          {/* Score Filter */}
          <select
            value={scoreFilter}
            onChange={(e) => setScoreFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
          >
            <option value="all">All Scores</option>
            <option value="high">High (80+)</option>
            <option value="mid">Mid (50-79)</option>
            <option value="low">Low (&lt;50)</option>
          </select>
        </div>
      </div>

      {/* Company Cards */}
      <div className="space-y-4">
        {filteredCompanies.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No companies found matching your filters.
          </div>
        ) : (
          filteredCompanies.map((company) => (
            <CompanyCard key={company.name} company={company} />
          ))
        )}
      </div>

      {/* Count */}
      <div className="mt-4 text-sm text-gray-500">
        Showing {filteredCompanies.length} of {companies.length} companies
      </div>
    </div>
  );
}
