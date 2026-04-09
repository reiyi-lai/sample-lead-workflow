// Utility functions for parsing and working with event dates

export interface ParsedDate {
  start: Date | null;
  end: Date | null;
}

/**
 * Parse event date strings that come in various formats:
 * - "January 26-28, 2026"
 * - "February 2-4, 2026"
 * - "April 20-22, 2026"
 * - "December 7-10, 2026"
 * - Single dates: "March 15, 2026"
 */
export function parseEventDate(dateString: string): ParsedDate {
  if (!dateString) return { start: null, end: null };

  try {
    // Clean the string
    const cleaned = dateString.trim();

    const parentheticalMatch = cleaned.match(/^(.+?)\s*\(.*\)$/);
    if (parentheticalMatch) {
      return parseEventDate(parentheticalMatch[1]);
    }

    if (cleaned.toLowerCase().startsWith('multiple dates:')) {
      const firstDate = cleaned.replace(/^multiple dates:\s*/i, '').split(',')[0].trim();
      return parseEventDate(firstDate);
    }

    const crossMonthMatch = cleaned.match(/^(\w+)\s+(\d+)\s*-\s*(\w+)\s+(\d+),\s+(\d{4})$/);
    if (crossMonthMatch) {
      const [, startMonth, startDay, endMonth, endDay, year] = crossMonthMatch;
      const startDate = new Date(`${startMonth} ${startDay}, ${year}`);
      const endDate = new Date(`${endMonth} ${endDay}, ${year}`);
      return { start: startDate, end: endDate };
    }

    const rangeMatch = cleaned.match(/^(\w+)\s+(\d+)-(\d+),\s+(\d{4})$/);
    if (rangeMatch) {
      const [, month, startDay, endDay, year] = rangeMatch;
      const startDate = new Date(`${month} ${startDay}, ${year}`);
      const endDate = new Date(`${month} ${endDay}, ${year}`);
      return { start: startDate, end: endDate };
    }

    const singleMatch = cleaned.match(/^(\w+)\s+(\d+),\s+(\d{4})$/);
    if (singleMatch) {
      const date = new Date(cleaned);
      return { start: date, end: date };
    }

    // Try direct parsing as fallback
    const fallbackDate = new Date(cleaned);
    if (!isNaN(fallbackDate.getTime())) {
      return { start: fallbackDate, end: fallbackDate };
    }

  } catch (error) {
    console.warn(`Failed to parse date: ${dateString}`, error);
  }

  return { start: null, end: null };
}

/**
 * Check if an event date falls within a given date range
 */
export function isEventInDateRange(
  eventDateString: string,
  filterStart: string,
  filterEnd: string
): boolean {
  const eventDate = parseEventDate(eventDateString);
  if (!eventDate.start) return false;

  const filterStartDate = new Date(filterStart);
  const filterEndDate = new Date(filterEnd);

  // Check if event overlaps with filter range
  // Event starts before filter ends AND event ends after filter starts
  const eventStartTime = eventDate.start.getTime();
  const eventEndTime = (eventDate.end || eventDate.start).getTime();
  const filterStartTime = filterStartDate.getTime();
  const filterEndTime = filterEndDate.getTime();

  return eventStartTime <= filterEndTime && eventEndTime >= filterStartTime;
}

/**
 * Format a Date object to YYYY-MM-DD for input[type="date"]
 */
export function formatDateForInput(date: Date): string {
  return date.toISOString().split('T')[0];
}