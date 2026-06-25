import { getAllOutreach } from "@/lib/data";
import OutreachList from "@/components/OutreachList";

export const dynamic = "force-dynamic";

export default function OutreachPage() {
  const allOutreach = getAllOutreach();

  return (
    <div className="p-8">
      <h1 className="text-xl font-semibold text-neutral-950 mb-6">Outreach</h1>
      <OutreachList contacts={allOutreach} />
    </div>
  );
}
