"use client";

import { useState } from "react";
import { CompanyWithDetails } from "@/lib/data";
import CompanyCard from "./CompanyCard";
import { Search } from "lucide-react";

interface CompanyListProps {
  companies: CompanyWithDetails[];
  events: string[];
}

export default function CompanyList({ companies, events }: CompanyListProps) {
  const [search, setSearch] = useState("");
  const [eventFilter, setEventFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");

  const filteredCompanies = companies.filter((company) => {
    if (search && !company.name.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    if (eventFilter !== "all" && company.event !== eventFilter) {
      return false;
    }
    if (scoreFilter === "high" && company.score < 80) return false;
    if (scoreFilter === "mid" && (company.score < 50 || company.score >= 80)) return false;
    if (scoreFilter === "low" && company.score >= 50) return false;
    return true;
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-neutral-950">Companies</h2>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
            className="px-3 py-2 border border-neutral-200 rounded-lg text-sm bg-white text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Events</option>
            {events.map((event) => (
              <option key={event} value={event}>{event}</option>
            ))}
          </select>

          <select
            value={scoreFilter}
            onChange={(e) => setScoreFilter(e.target.value)}
            className="px-3 py-2 border border-neutral-200 rounded-lg text-sm bg-white text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Scores</option>
            <option value="high">High (80+)</option>
            <option value="mid">Mid (50-79)</option>
            <option value="low">Low (&lt;50)</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        {filteredCompanies.length === 0 ? (
          <div className="text-center py-12 text-neutral-500 text-sm">
            No companies found matching your filters.
          </div>
        ) : (
          filteredCompanies.map((company) => (
            <CompanyCard key={company.name} company={company} />
          ))
        )}
      </div>

      <div className="mt-4 text-xs text-neutral-500">
        {filteredCompanies.length} of {companies.length} companies
      </div>
    </div>
  );
}
