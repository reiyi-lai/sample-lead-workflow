import { getSupabaseCompaniesWithDetails } from "@/lib/supabaseCompanies";
import OutreachList from "@/components/OutreachList";

export const dynamic = "force-dynamic";

export default async function ContactsPage({
  searchParams,
}: {
  searchParams: Promise<{ company?: string }>;
}) {
  const { company } = await searchParams;
  const companies = await getSupabaseCompaniesWithDetails();
  const contacts = companies
    .filter((item) => !company || item.name === company)
    .flatMap((item) => item.contacts);

  return (
    <div className="p-8">
      <h1 className="text-xl font-semibold text-neutral-950 mb-6">Contacts & Outreach</h1>
      <OutreachList contacts={contacts} />
    </div>
  );
}
