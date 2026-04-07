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
  availableIndustries: string[];
}

export default function EventsFilters({
  onDateRangeChange,
  onIndustryChange,
  onScoringTypeChange,
  availableIndustries
}: EventsFiltersProps) {
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [selectedIndustry, setSelectedIndustry] = useState<string>("");
  const [selectedScoringType, setSelectedScoringType] = useState<string>("");

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

  const handleScoringTypeChange = (type: string) => {
    setSelectedScoringType(type);
    onScoringTypeChange(type || null);
  };

  const clearScoringTypeFilter = () => {
    setSelectedScoringType("");
    onScoringTypeChange(null);
  };

  const formatIndustryLabel = (industry: string) => {
    if (!industry) return "All Industries";
    if (industry === "others") return "Others";
    return industry.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <h3 className="font-semibold text-gray-900 mb-4">Filters</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Date Range Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Event Date
          </label>
          <div className="space-y-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => handleStartDateChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-500"
                min="2026-01-01"
                max="2026-12-31"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => handleEndDateChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-500"
                min="2026-01-01"
                max="2026-12-31"
              />
            </div>
            {(startDate || endDate) && (
              <button
                onClick={clearDateFilter}
                className="text-xs text-blue-600 hover:text-blue-800 underline"
              >
                Clear date filter
              </button>
            )}
          </div>
        </div>

        {/* Industry Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Industry Vertical
          </label>
          <select
            value={selectedIndustry}
            onChange={(e) => handleIndustryChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-900 bg-white"
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
              className="text-xs text-blue-600 hover:text-blue-800 underline mt-1"
            >
              Clear industry filter
            </button>
          )}
        </div>

        {/* Scoring Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Event Type
          </label>
          <select
            value={selectedScoringType}
            onChange={(e) => handleScoringTypeChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-900 bg-white"
          >
            <option value="">All Types</option>
            <option value="supply_chain">Supply Chain</option>
            <option value="industry_specific">Industry-Specific</option>
          </select>
          {selectedScoringType && (
            <button
              onClick={clearScoringTypeFilter}
              className="text-xs text-blue-600 hover:text-blue-800 underline mt-1"
            >
              Clear type filter
            </button>
          )}
        </div>
      </div>
    </div>
  );
}