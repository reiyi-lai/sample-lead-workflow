"use client";

import { useState } from "react";
import { ContactWithOutreach } from "@/lib/data";
import OutreachPreviewModal from "./OutreachPreviewModal";

interface EnrichedContact extends ContactWithOutreach {
  tier: number;
}

interface OutreachListProps {
  contacts: EnrichedContact[];
}

export default function OutreachList({ contacts }: OutreachListProps) {
  const [selectedContact, setSelectedContact] = useState<EnrichedContact | null>(null);

  // Filter contacts with outreach
  const contactsWithOutreach = contacts.filter((c) => c.outreach);

  const tierColors: Record<number, string> = {
    1: "bg-green-100 text-green-800",
    2: "bg-yellow-100 text-yellow-800",
    3: "bg-gray-100 text-gray-800",
  };

  return (
    <div>
      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {contactsWithOutreach.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No outreach messages found.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Contact
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Company
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Channel
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {contactsWithOutreach.map((contact) => (
                <tr key={contact.name} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <div>
                      <p className="font-medium text-gray-900">{contact.name}</p>
                      <p className="text-sm text-gray-500">{contact.title}</p>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-900">{contact.company}</span>
                      {contact.tier > 0 && (
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            tierColors[contact.tier] || tierColors[3]
                          }`}
                        >
                          Tier {contact.tier}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        contact.outreach?.channel === "email"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-indigo-100 text-indigo-700"
                      }`}
                    >
                      {contact.outreach?.channel || "Email"}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <button
                      onClick={() => setSelectedContact(contact)}
                      className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Preview
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Count */}
      <div className="mt-4 text-sm text-gray-500">
        {contactsWithOutreach.length} outreach messages
      </div>

      {/* Preview Modal */}
      {selectedContact && (
        <OutreachPreviewModal
          contact={selectedContact}
          onClose={() => setSelectedContact(null)}
        />
      )}
    </div>
  );
}
