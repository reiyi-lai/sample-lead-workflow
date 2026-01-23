import { getAllOutreach, getAllCompaniesWithDetails } from "@/lib/data";
import OutreachList from "@/components/OutreachList";

export const dynamic = "force-dynamic";

export default function OutreachPage() {
  const allOutreach = getAllOutreach();
  const companies = getAllCompaniesWithDetails();

  // Enrich outreach with company tier
  const enrichedOutreach = allOutreach.map((contact) => {
    const company = companies.find((c) => c.name === contact.company);
    return {
      ...contact,
      tier: company?.tier || 0,
    };
  });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-6">Outreach</h1>
      <OutreachList contacts={enrichedOutreach} />
    </div>
  );
}
