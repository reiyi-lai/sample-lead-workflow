import { getScoredEvents, getEventCompanies } from "@/lib/data";
import EventsList from "@/components/EventsList";

export const dynamic = "force-dynamic";

export default function EventsPage() {
  const scoredEvents = getScoredEvents();
  const eventCompanies = getEventCompanies();

  // Combine scored events with their company data
  const events = (scoredEvents?.qualified_events || []).map((event) => {
    const companyData = eventCompanies.find(
      (ec) => ec.event_name === event.event_name
    );
    return {
      ...event,
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
