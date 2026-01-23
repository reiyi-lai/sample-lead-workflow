interface StatsCardsProps {
  stats: {
    events: number;
    companies: number;
    contacts: number;
    messages: number;
  };
}

export default function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    { label: "Events", value: stats.events},
    { label: "Companies", value: stats.companies},
    { label: "Contacts", value: stats.contacts},
    { label: "Messages", value: stats.messages},
  ];

  return (
    <div className="grid grid-cols-4 gap-6">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
        >
          <div className="mt-1">
            <p className="text-3xl font-bold text-gray-900">{card.value}</p>
            <p className="text-sm text-gray-500 mt-1">{card.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
