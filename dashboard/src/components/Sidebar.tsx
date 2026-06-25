"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CalendarDays } from "lucide-react";

const navItems = [
  { href: "/", label: "Events", icon: CalendarDays },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-neutral-950 flex flex-col">
      <div className="px-6 py-8">
        <h1 className="text-xl font-semibold text-white tracking-tight pb-1">Instalily</h1>
        <p className="text-sm text-neutral-400 mt-0.5">GTM Pipeline</p>
      </div>

      <nav className="flex-1 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    isActive
                      ? "bg-white text-neutral-950 font-medium"
                      : "text-neutral-400 hover:text-white hover:bg-neutral-800/60"
                  }`}
                >
                  <Icon size={16} strokeWidth={isActive ? 2.5 : 1.5} />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="px-6 py-4">
        <p className="text-[10px] text-neutral-600 uppercase tracking-widest">
          Instalily GTM
        </p>
      </div>
    </aside>
  );
}
