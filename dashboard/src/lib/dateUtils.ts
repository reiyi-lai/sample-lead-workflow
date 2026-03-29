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

    // Handle range formats like "January 26-28, 2026" or "February 2-4, 2026"
    const rangeMatch = cleaned.match(/^(\w+)\s+(\d+)-(\d+),\s+(\d+)$/);
    if (rangeMatch) {
      const [, month, startDay, endDay, year] = rangeMatch;
      const startDate = new Date(`${month} ${startDay}, ${year}`);
      const endDate = new Date(`${month} ${endDay}, ${year}`);
      return { start: startDate, end: endDate };
    }

    // Handle single date formats like "March 15, 2026"
    const singleMatch = cleaned.match(/^(\w+)\s+(\d+),\s+(\d+)$/);
    if (singleMatch) {
      const date = new Date(cleaned);
      return { start: date, end: date };
    }

    // Handle multi-day formats like "April 13-16, 2026"
    const multiDayMatch = cleaned.match(/^(\w+)\s+(\d+)-(\d+),\s+(\d+)$/);
    if (multiDayMatch) {
      const [, month, startDay, endDay, year] = multiDayMatch;
      const startDate = new Date(`${month} ${startDay}, ${year}`);
      const endDate = new Date(`${month} ${endDay}, ${year}`);
      return { start: startDate, end: endDate };
    }

    // Handle formats with different months like "January 20-23, 2026 (typical timing)"
    const parentheticalMatch = cleaned.match(/^(.+?)\s*\(.*\)$/);
    if (parentheticalMatch) {
      return parseEventDate(parentheticalMatch[1]);
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