"use client";

import { useState } from "react";

interface DateRange {
  start: string;
  end: string;
}

interface EventsFiltersProps {
  onDateRangeChange: (dateRange: DateRange | null) => void;
  onIndustryChange: (industry: string | null) => void;
  availableIndustries: string[];
}

export default function EventsFilters({
  onDateRangeChange,
  onIndustryChange,
  availableIndustries
}: EventsFiltersProps) {
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [selectedIndustry, setSelectedIndustry] = useState<string>("");

  const handleStartDateChange = (date: string) => {
    setStartDate(date);
    updateDateRange(date, endDate);
  };

  const handleEndDateChange = (date: string) => {
    setEndDate(date);
    updateDateRange(startDate, date);
  };

  const updateDateRange = (start: string, end: string) => {
    if (start && end) {
      onDateRangeChange({ start, end });
    } else if (!start && !end) {
      onDateRangeChange(null);
    }
  };

  const handleIndustryChange = (industry: string) => {
    setSelectedIndustry(industry);
    onIndustryChange(industry || null);
  };

  const clearDateFilter = () => {
    setStartDate("");
    setEndDate("");
    onDateRangeChange(null);
  };

  const clearIndustryFilter = () => {
    setSelectedIndustry("");
    onIndustryChange(null);
  };

  const formatIndustryLabel = (industry: string) => {
    if (!industry) return "All Industries";
    if (industry === "others") return "Others";
    return industry.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="border border-neutral-200 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-medium text-neutral-950 mb-4 uppercase tracking-wide">Filters</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-neutral-500 mb-2">
            Event Date
          </label>
          <div className="space-y-2">
            <div>
              <label className="block text-[10px] text-neutral-500 mb-1 uppercase tracking-wide">Start</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => handleStartDateChange(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
                min="2026-01-01"
                max="2026-12-31"
              />
            </div>
            <div>
              <label className="block text-[10px] text-neutral-500 mb-1 uppercase tracking-wide">End</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => handleEndDateChange(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
                min="2026-01-01"
                max="2026-12-31"
              />
            </div>
            {(startDate || endDate) && (
              <button
                onClick={clearDateFilter}
                className="text-xs text-neutral-500 hover:text-neutral-950 underline underline-offset-2"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-neutral-500 mb-2">
            Industry Vertical
          </label>
          <select
            value={selectedIndustry}
            onChange={(e) => handleIndustryChange(e.target.value)}
            className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 bg-white focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
          >
            <option value="">All Industries</option>
            {availableIndustries.map((industry) => (
              <option key={industry} value={industry}>
                {formatIndustryLabel(industry)}
              </option>
            ))}
          </select>
          {selectedIndustry && (
            <button
              onClick={clearIndustryFilter}
              className="text-xs text-neutral-500 hover:text-neutral-950 underline underline-offset-2 mt-1"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
