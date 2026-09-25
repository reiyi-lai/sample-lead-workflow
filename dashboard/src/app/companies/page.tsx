import { getSupabaseCompaniesWithDetails, getSupabaseCompanyStats } from "@/lib/supabaseCompanies";
import StatsCards from "@/components/StatsCards";
import CompanyList from "@/components/CompanyList";

export const dynamic = "force-dynamic";

export default async function CompaniesPage() {
  const companies = await getSupabaseCompaniesWithDetails();
  const stats = await getSupabaseCompanyStats(companies);
  const events = [...new Set(companies.flatMap((company) => company.events || []))].sort();

  return (
    <div className="p-8">
      <StatsCards stats={stats} />
      <div className="mt-8">
        <CompanyList companies={companies} events={events} />
      </div>
    </div>
  );
}
