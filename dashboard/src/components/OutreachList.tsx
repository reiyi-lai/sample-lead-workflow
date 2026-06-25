"use client";

import { useState } from "react";
import { ContactWithOutreach } from "@/lib/data";
import OutreachPreviewModal from "./OutreachPreviewModal";

interface ContactInput {
  name: string;
  linkedinUrl: string;
  email: string;
}

interface OutreachListProps {
  contacts: ContactWithOutreach[];
}

export default function OutreachList({ contacts }: OutreachListProps) {
  const [contactsWithOutreach, setContactsWithOutreach] = useState(
    () => contacts.filter((c) => c.outreach)
  );
  const [selectedContact, setSelectedContact] = useState<ContactWithOutreach | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [input, setInput] = useState<ContactInput>({ name: "", linkedinUrl: "", email: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isPlaceholder = (name: string) => !name || name === "[Name]";

  const handleSave = async (contact: ContactWithOutreach, index: number) => {
    if (!input.name.trim()) return;

    setSaving(true);
    setError("");

    try {
      const res = await fetch("/api/assign-contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyName: contact.company,
          roleTitle: contact.title,
          contactName: input.name.trim(),
          linkedinUrl: input.linkedinUrl.trim() || undefined,
          email: input.email.trim() || undefined,
        }),
      });

      const data = await res.json();

      if (data.success) {
        setContactsWithOutreach((prev) =>
          prev.map((c, i) => i === index ? { ...c, name: input.name.trim() } : c)
        );
        setEditingIndex(null);
        setInput({ name: "", linkedinUrl: "", email: "" });
      } else {
        setError(data.error || "Failed to save");
      }
    } catch {
      setError("Network error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="border border-neutral-200 rounded-lg overflow-hidden">
        {contactsWithOutreach.length === 0 ? (
          <div className="p-12 text-center text-neutral-500 text-sm">
            No outreach messages found.
          </div>
        ) : (
          <table className="w-full">
            <thead className="border-b border-neutral-200">
              <tr>
                <th className="px-4 py-3 text-left text-[10px] font-medium text-neutral-500 uppercase tracking-wide">
                  Role / Contact
                </th>
                <th className="px-4 py-3 text-left text-[10px] font-medium text-neutral-500 uppercase tracking-wide">
                  Company
                </th>
                <th className="px-4 py-3 text-left text-[10px] font-medium text-neutral-500 uppercase tracking-wide">
                  Channel
                </th>
                <th className="px-4 py-3 text-right text-[10px] font-medium text-neutral-500 uppercase tracking-wide">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {contactsWithOutreach.map((contact, index) => {
                const placeholder = isPlaceholder(contact.name);

                return (
                  <tr key={`${contact.company}-${contact.title}-${index}`} className="hover:bg-neutral-50">
                    <td className="px-4 py-3.5">
                      <div>
                        <p className="text-sm font-medium text-neutral-900">{contact.title}</p>
                        <p className="text-xs text-neutral-500 mt-0.5">
                          {placeholder ? "No contact assigned" : contact.name}
                        </p>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-sm text-neutral-900">{contact.company}</span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wide border border-neutral-200 text-neutral-500">
                        {contact.outreach?.channel || "Email"}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {placeholder ? (
                          <button
                            onClick={() => {
                              setEditingIndex(index);
                              setInput({ name: "", linkedinUrl: "", email: "" });
                              setError("");
                            }}
                            className="px-3 py-1.5 text-xs font-medium text-neutral-950 border border-neutral-200 rounded-md hover:bg-neutral-100 transition-colors"
                          >
                            Add Contact
                          </button>
                        ) : (
                          <button
                            onClick={() => {
                              setEditingIndex(index);
                              setInput({ name: contact.name, linkedinUrl: "", email: "" });
                              setError("");
                            }}
                            className="px-3 py-1.5 text-xs font-medium text-neutral-600 border border-neutral-200 rounded-md hover:bg-neutral-100 transition-colors"
                          >
                            Edit
                          </button>
                        )}
                        <button
                          onClick={() => setSelectedContact(contact)}
                          className="px-3 py-1.5 text-xs font-medium text-white bg-neutral-950 rounded-md hover:bg-neutral-800 transition-colors"
                        >
                          Preview
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="mt-4 text-xs text-neutral-500">
        {contactsWithOutreach.length} outreach messages
      </div>

      {selectedContact && (
        <OutreachPreviewModal
          contact={selectedContact}
          onClose={() => setSelectedContact(null)}
        />
      )}

      {editingIndex !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setEditingIndex(null)}
          />
          <div className="relative bg-white rounded-lg border border-neutral-200 shadow-2xl max-w-md w-full mx-4 p-6">
            <h3 className="text-base font-semibold text-neutral-950 mb-0.5">
              {editingIndex !== null && !isPlaceholder(contactsWithOutreach[editingIndex]?.name)
                ? "Edit Contact"
                : "Add Contact"}
            </h3>
            <p className="text-xs text-neutral-500 mb-5">
              {contactsWithOutreach[editingIndex]?.title} at{" "}
              {contactsWithOutreach[editingIndex]?.company}
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">
                  Name *
                </label>
                <input
                  type="text"
                  value={input.name}
                  onChange={(e) => setInput({ ...input, name: e.target.value })}
                  placeholder="e.g. Laura Noll"
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
                />
              </div>
              <div>
                <label className="block text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">
                  LinkedIn URL
                </label>
                <input
                  type="text"
                  value={input.linkedinUrl}
                  onChange={(e) => setInput({ ...input, linkedinUrl: e.target.value })}
                  placeholder="https://linkedin.com/in/..."
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
                />
              </div>
              <div>
                <label className="block text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">
                  Email
                </label>
                <input
                  type="text"
                  value={input.email}
                  onChange={(e) => setInput({ ...input, email: e.target.value })}
                  placeholder="laura@company.com"
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-neutral-500 focus:border-neutral-500"
                />
              </div>

              {error && <p className="text-xs text-red-600">{error}</p>}

              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={() => handleSave(contactsWithOutreach[editingIndex], editingIndex)}
                  disabled={!input.name.trim() || saving}
                  className={`px-4 py-2 text-xs font-medium rounded-md transition-colors ${
                    input.name.trim() && !saving
                      ? "bg-neutral-950 text-white hover:bg-neutral-800"
                      : "bg-neutral-100 text-neutral-300 cursor-not-allowed"
                  }`}
                >
                  {saving ? "Saving..." : "Save"}
                </button>
                <button
                  onClick={() => setEditingIndex(null)}
                  className="px-4 py-2 text-xs text-neutral-500 hover:text-neutral-600"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
