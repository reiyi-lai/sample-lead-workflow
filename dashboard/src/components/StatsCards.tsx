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
    { label: "Events", value: stats.events },
    { label: "Companies", value: stats.companies },
    { label: "Contacts", value: stats.contacts },
    { label: "Messages", value: stats.messages },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="border border-neutral-200 rounded-lg p-5"
        >
          <p className="text-3xl font-semibold text-neutral-950 tracking-tight">{card.value}</p>
          <p className="text-xs text-neutral-600 mt-1 uppercase tracking-wide">{card.label}</p>
        </div>
      ))}
    </div>
  );
}
