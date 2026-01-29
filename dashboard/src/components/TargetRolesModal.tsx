"use client";

import { useState } from "react";
import { CompanyWithDetails, LinkedInSearch } from "@/lib/data";

interface ContactInput {
  name: string;
  linkedinUrl: string;
  email: string;
}

interface TargetRolesModalProps {
  company: CompanyWithDetails;
  onClose: () => void;
}

export default function TargetRolesModal({ company, onClose }: TargetRolesModalProps) {
  const targetRoles = company.targetRoles;

  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Record<string, ContactInput>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!targetRoles) return null;

  // Match contacts to roles by title
  const getContactForRole = (roleTitle: string) => {
    return company.contacts.find(
      (c) =>
        c.title.toLowerCase().includes(roleTitle.toLowerCase()) ||
        roleTitle.toLowerCase().includes(c.title.toLowerCase())
    );
  };

  // Match LinkedIn search URL to role by title
  const getSearchUrlForRole = (roleTitle: string) => {
    return company.linkedInSearches.find(
      (s) => s.role_title.toLowerCase() === roleTitle.toLowerCase()
    )?.search_url;
  };

  const getInput = (roleTitle: string): ContactInput => {
    return inputs[roleTitle] || { name: "", linkedinUrl: "", email: "" };
  };

  const updateInput = (roleTitle: string, field: keyof ContactInput, value: string) => {
    setInputs((prev) => ({
      ...prev,
      [roleTitle]: { ...getInput(roleTitle), [field]: value },
    }));
  };

  const handleSave = async (roleTitle: string) => {
    const input = getInput(roleTitle);
    if (!input.name.trim()) return;

    setSaving(roleTitle);
    setErrors((prev) => ({ ...prev, [roleTitle]: "" }));

    try {
      const res = await fetch("/api/assign-contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyName: company.name,
          roleTitle,
          contactName: input.name.trim(),
          linkedinUrl: input.linkedinUrl.trim() || undefined,
          email: input.email.trim() || undefined,
        }),
      });

      const data = await res.json();

      if (data.success) {
        setSaved((prev) => ({ ...prev, [roleTitle]: true }));
        setExpandedRole(null);
      } else {
        setErrors((prev) => ({ ...prev, [roleTitle]: data.error || "Failed to save" }));
      }
    } catch (e) {
      setErrors((prev) => ({ ...prev, [roleTitle]: "Network error" }));
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Target Roles</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {targetRoles.target_roles.map((role, index) => {
            const contact = getContactForRole(role.title);
            const searchUrl = getSearchUrlForRole(role.title);
            const isExpanded = expandedRole === role.title;
            const isSaved = saved[role.title];
            const input = getInput(role.title);
            const error = errors[role.title];

            return (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4"
              >
                {/* Role Header */}
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{role.title}</h3>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                    Priority {role.priority}
                  </span>
                </div>

                {/* LinkedIn Sales Nav Search */}
                {searchUrl && (
                  <a
                    href={searchUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mb-3 text-sm text-blue-600 hover:underline"
                  >
                    LinkedIn Sales Nav Search →
                  </a>
                )}

                {/* Rationale */}
                <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                  {role.rationale}
                </p>

                {/* Contact Assignment Section */}
                <div className="mt-4 pt-3 border-t border-gray-100">
                  {contact && !isSaved && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-600">
                        Contact: <span className="font-medium text-gray-900">{contact.name}</span>
                      </span>
                    </div>
                  )}

                  {isSaved && (
                    <div className="flex items-center gap-2 text-sm text-green-700">
                      <span>Contact assigned: <span className="font-medium">{input.name}</span></span>
                      {input.email && <span className="text-gray-400">• {input.email}</span>}
                    </div>
                  )}

                  {!contact && !isSaved && !isExpanded && (
                    <button
                      onClick={() => setExpandedRole(role.title)}
                      className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                      + Add Contact
                    </button>
                  )}

                  {isExpanded && (
                    <div className="mt-3 space-y-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Contact Name *
                        </label>
                        <input
                          type="text"
                          value={input.name}
                          onChange={(e) => updateInput(role.title, "name", e.target.value)}
                          placeholder="e.g. Laura Noll"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          LinkedIn URL (optional)
                        </label>
                        <input
                          type="text"
                          value={input.linkedinUrl}
                          onChange={(e) => updateInput(role.title, "linkedinUrl", e.target.value)}
                          placeholder="https://linkedin.com/in/..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">
                          Email (optional)
                        </label>
                        <input
                          type="text"
                          value={input.email}
                          onChange={(e) => updateInput(role.title, "email", e.target.value)}
                          placeholder="laura@company.com"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      {error && (
                        <p className="text-sm text-red-600">{error}</p>
                      )}

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleSave(role.title)}
                          disabled={!input.name.trim() || saving === role.title}
                          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                            input.name.trim() && saving !== role.title
                              ? "bg-blue-600 text-white hover:bg-blue-700"
                              : "bg-gray-200 text-gray-400 cursor-not-allowed"
                          }`}
                        >
                          {saving === role.title ? "Saving..." : "Save Contact"}
                        </button>
                        <button
                          onClick={() => setExpandedRole(null)}
                          className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {targetRoles.target_roles.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              No target roles defined for this company.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
