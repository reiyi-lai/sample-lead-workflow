import { getDashboardStats, getAllCompaniesWithDetails, getUniqueEvents } from "@/lib/data";
import StatsCards from "@/components/StatsCards";
import CompanyList from "@/components/CompanyList";

export const dynamic = "force-dynamic";

export default function CompaniesPage() {
  const stats = getDashboardStats();
  const companies = getAllCompaniesWithDetails();
  const events = getUniqueEvents();

  return (
    <div className="p-8">
      {/* Stats Cards */}
      <StatsCards stats={stats} />

      {/* Companies Section */}
      <div className="mt-8">
        <CompanyList companies={companies} events={events} />
      </div>
    </div>
  );
}
