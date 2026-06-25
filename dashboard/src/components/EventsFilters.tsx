"use client";

import { useState } from "react";

interface DateRange {
  start: string;
  end: string;
}

interface EventsFiltersProps {
  onDateRangeChange: (dateRange: DateRange | null) => void;
  onIndustryChange: (industry: string | null) => void;
  onScoringTypeChange: (scoringType: string | null) => void;
  onAttendingFilterChange: (attending: boolean | null) => void;
  availableIndustries: string[];
}

export default function EventsFilters({
  onDateRangeChange,
  onIndustryChange,
  onScoringTypeChange,
  onAttendingFilterChange,
  availableIndustries
}: EventsFiltersProps) {
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [selectedIndustry, setSelectedIndustry] = useState<string>("");
  const [selectedScoringType, setSelectedScoringType] = useState<string>("");
  const [selectedAttending, setSelectedAttending] = useState<string>("");

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

  const handleScoringTypeChange = (type: string) => {
    setSelectedScoringType(type);
    onScoringTypeChange(type || null);
  };

  const handleAttendingChange = (val: string) => {
    setSelectedAttending(val);
    onAttendingFilterChange(val === "" ? null : val === "yes");
  };

  const clearDateFilter = () => {
    setStartDate("");
    setEndDate("");
    onDateRangeChange(null);
  };

  const formatIndustryLabel = (industry: string) => {
    if (!industry) return "All Industries";
    return industry.split(",")[0].trim().replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="border border-neutral-200 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-medium text-neutral-950 mb-4 uppercase tracking-wide">Filters</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
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
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
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

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-neutral-500 mb-2">
              Event Type
            </label>
            <select
              value={selectedScoringType}
              onChange={(e) => handleScoringTypeChange(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="supply_chain">Supply Chain</option>
              <option value="industry_specific">Industry-Specific</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-neutral-500 mb-2">
              Attending?
            </label>
            <select
              value={selectedAttending}
              onChange={(e) => handleAttendingChange(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
              <option value="it_depends">Depends</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-neutral-500 mb-2">
            Industry Vertical
          </label>
          <select
            value={selectedIndustry}
            onChange={(e) => handleIndustryChange(e.target.value)}
            className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Industries</option>
            {availableIndustries.map((industry) => (
              <option key={industry} value={industry}>
                {formatIndustryLabel(industry)}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
