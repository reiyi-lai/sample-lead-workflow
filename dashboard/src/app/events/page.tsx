import { getScoredEvents, getEventCompanies, getDiscoveredEvents } from "@/lib/data";
import EventsList from "@/components/EventsList";

export const dynamic = "force-dynamic";

export default function EventsPage() {
  const scoredEvents = getScoredEvents();
  const discoveredEvents = getDiscoveredEvents();
  const eventCompanies = getEventCompanies();

  // Combine discovered events with scoring data and company data
  const events = discoveredEvents.map((discoveredEvent) => {
    const scoreData = scoredEvents?.scored_events?.find(
      (scoredEvent) => scoredEvent.event_name === discoveredEvent.event_name
    );
    const companyData = eventCompanies.find(
      (ec) => ec.event_name === discoveredEvent.event_name
    );

    return {
      ...discoveredEvent, // All the rich event details (dates, location, venue, cost, etc.)
      ...scoreData,       // Scoring information (overall_score, scores)
      companies: companyData?.companies || [],
      totalConfirmed: companyData?.total_confirmed || 0,
      totalLikely: companyData?.total_likely || 0,
    };
  });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-1">Events</h1>
      <EventsList events={events} />
    </div>
  );
}
