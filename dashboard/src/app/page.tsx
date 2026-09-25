import { getSupabaseEvents } from "@/lib/supabaseData";
import EventsList from "@/components/EventsList";

export const dynamic = "force-dynamic";

export default async function EventsPage() {
  const events = await getSupabaseEvents();

  return (
    <div className="p-8">
      <h1 className="text-xl font-semibold text-neutral-950 mb-6">Events</h1>
      <EventsList events={events} />
    </div>
  );
}
