import { getEnrichedEvents } from "@/lib/data";
import EventsList from "@/components/EventsList";

export const dynamic = "force-dynamic";

export default async function EventsPage() {
  const events = getEnrichedEvents();

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-1">Events</h1>
      <EventsList events={events} />
    </div>
  );
}
