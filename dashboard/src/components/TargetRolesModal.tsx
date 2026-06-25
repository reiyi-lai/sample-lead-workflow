"use client";

import { useState } from "react";
import { CompanyWithDetails, LinkedInSearch } from "@/lib/data";
import { X, ExternalLink } from "lucide-react";

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

  const getContactForRole = (roleTitle: string) => {
    return company.contacts.find(
      (c) =>
        c.title.toLowerCase().includes(roleTitle.toLowerCase()) ||
        roleTitle.toLowerCase().includes(c.title.toLowerCase())
    );
  };

  const getSearchUrlForRole = (roleTitle: string) => {
    return company.linkedInSearches.find(
      (s: LinkedInSearch) => s.role_title.toLowerCase() === roleTitle.toLowerCase()
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
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative bg-white rounded-lg border border-neutral-200 shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200">
          <h2 className="text-base font-semibold text-neutral-950">Target Roles</h2>
          <button
            onClick={onClose}
            className="text-neutral-500 hover:text-neutral-700 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-6 py-5 overflow-y-auto space-y-4">
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
                className="border border-neutral-200 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-semibold text-neutral-950">{role.title}</h3>
                  <span className="px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide border border-neutral-200 text-neutral-500 rounded-full">
                    Priority {role.priority}
                  </span>
                </div>

                {searchUrl && (
                  <a
                    href={searchUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mb-2 text-xs text-neutral-500 hover:text-neutral-950 transition-colors"
                  >
                    LinkedIn Sales Nav
                    <ExternalLink size={10} />
                  </a>
                )}

                <p className="text-xs text-neutral-500 leading-relaxed whitespace-pre-wrap">
                  {role.rationale}
                </p>

                <div className="mt-3 pt-3 border-t border-neutral-100">
                  {contact && !isSaved && (
                    <div className="text-xs text-neutral-500">
                      Contact: <span className="font-medium text-neutral-900">{contact.name}</span>
                    </div>
                  )}

                  {isSaved && (
                    <div className="text-xs text-neutral-500">
                      Assigned: <span className="font-medium text-neutral-900">{input.name}</span>
                      {input.email && <span className="text-neutral-500 ml-2">{input.email}</span>}
                    </div>
                  )}

                  {!contact && !isSaved && !isExpanded && (
                    <button
                      onClick={() => setExpandedRole(role.title)}
                      className="text-xs font-medium text-neutral-950 hover:text-neutral-600"
                    >
                      + Add Contact
                    </button>
                  )}

                  {isExpanded && (
                    <div className="mt-3 space-y-3">
                      <div>
                        <label className="block text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">
                          Name *
                        </label>
                        <input
                          type="text"
                          value={input.name}
                          onChange={(e) => updateInput(role.title, "name", e.target.value)}
                          placeholder="e.g. Laura Noll"
                          className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">
                          LinkedIn URL
                        </label>
                        <input
                          type="text"
                          value={input.linkedinUrl}
                          onChange={(e) => updateInput(role.title, "linkedinUrl", e.target.value)}
                          placeholder="https://linkedin.com/in/..."
                          className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">
                          Email
                        </label>
                        <input
                          type="text"
                          value={input.email}
                          onChange={(e) => updateInput(role.title, "email", e.target.value)}
                          placeholder="laura@company.com"
                          className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      {error && <p className="text-xs text-red-600">{error}</p>}

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleSave(role.title)}
                          disabled={!input.name.trim() || saving === role.title}
                          className={`px-4 py-2 text-xs font-medium rounded-md transition-colors ${
                            input.name.trim() && saving !== role.title
                              ? "bg-neutral-950 text-white hover:bg-neutral-800"
                              : "bg-neutral-100 text-neutral-300 cursor-not-allowed"
                          }`}
                        >
                          {saving === role.title ? "Saving..." : "Save"}
                        </button>
                        <button
                          onClick={() => setExpandedRole(null)}
                          className="px-4 py-2 text-xs text-neutral-500 hover:text-neutral-700"
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
            <p className="text-center text-neutral-500 text-sm py-8">
              No target roles defined for this company.
            </p>
          )}
        </div>

        <div className="px-6 py-3 border-t border-neutral-200">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-xs font-medium border border-neutral-200 text-neutral-600 rounded-md hover:bg-neutral-100 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
