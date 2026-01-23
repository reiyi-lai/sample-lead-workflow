"use client";

import { CompanyWithDetails } from "@/lib/data";

interface TargetRolesModalProps {
  company: CompanyWithDetails;
  onClose: () => void;
}

export default function TargetRolesModal({ company, onClose }: TargetRolesModalProps) {
  const targetRoles = company.targetRoles;

  if (!targetRoles) return null;

  // Match contacts to roles by title
  const getContactForRole = (roleTitle: string) => {
    return company.contacts.find(
      (c) => c.title.toLowerCase().includes(roleTitle.toLowerCase()) ||
             roleTitle.toLowerCase().includes(c.title.toLowerCase())
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">
            Target Roles
          </h2>
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

                {/* Rationale */}
                <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                  {role.rationale}
                </p>

                {/* Contact if found */}
                {contact && (
                  <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-2 text-sm">
                    <span className="text-gray-400">📧</span>
                    <span className="text-gray-600">
                      Contact: <span className="font-medium text-gray-900">{contact.name}</span>
                    </span>
                  </div>
                )}
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
