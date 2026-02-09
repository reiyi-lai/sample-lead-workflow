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
                  Role / Contact
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
              {contactsWithOutreach.map((contact, index) => {
                const placeholder = isPlaceholder(contact.name);

                return (
                  <tr key={`${contact.company}-${contact.title}-${index}`} className="hover:bg-gray-50">
                    <td className="px-4 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{contact.title}</p>
                        <p className="text-sm text-gray-500">
                          {placeholder ? "No contact assigned" : contact.name}
                        </p>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-gray-900">{contact.company}</span>
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
                      <div className="flex items-center justify-end gap-2">
                        {placeholder ? (
                          <button
                            onClick={() => {
                              setEditingIndex(index);
                              setInput({ name: "", linkedinUrl: "", email: "" });
                              setError("");
                            }}
                            className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
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
                            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                          >
                            Edit Contact
                          </button>
                        )}
                        <button
                          onClick={() => setSelectedContact(contact)}
                          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
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

      {/* Add Contact Modal */}
      {editingIndex !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setEditingIndex(null)}
          />
          <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-1">
              {editingIndex !== null && !isPlaceholder(contactsWithOutreach[editingIndex]?.name)
                ? "Edit Contact Details"
                : "Add Contact Details"}
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              {contactsWithOutreach[editingIndex]?.title} at{" "}
              {contactsWithOutreach[editingIndex]?.company}
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Contact Name *
                </label>
                <input
                  type="text"
                  value={input.name}
                  onChange={(e) => setInput({ ...input, name: e.target.value })}
                  placeholder="e.g. Laura Noll"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  LinkedIn URL (optional)
                </label>
                <input
                  type="text"
                  value={input.linkedinUrl}
                  onChange={(e) => setInput({ ...input, linkedinUrl: e.target.value })}
                  placeholder="https://linkedin.com/in/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Email (optional)
                </label>
                <input
                  type="text"
                  value={input.email}
                  onChange={(e) => setInput({ ...input, email: e.target.value })}
                  placeholder="laura@company.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={() => handleSave(contactsWithOutreach[editingIndex], editingIndex)}
                  disabled={!input.name.trim() || saving}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    input.name.trim() && !saving
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-gray-200 text-gray-400 cursor-not-allowed"
                  }`}
                >
                  {saving ? "Saving..." : "Save Contact"}
                </button>
                <button
                  onClick={() => setEditingIndex(null)}
                  className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700"
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
