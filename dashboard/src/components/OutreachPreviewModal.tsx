"use client";

import { ContactWithOutreach } from "@/lib/data";

interface OutreachPreviewModalProps {
  contact: ContactWithOutreach;
  onClose: () => void;
}

export default function OutreachPreviewModal({
  contact,
  onClose,
}: OutreachPreviewModalProps) {
  const outreach = contact.outreach;
  const channel = outreach?.channel || "email";
  const isEmail = channel === "email";

  const handleCopy = () => {
    if (outreach?.message?.body) {
      const text = isEmail
        ? `Subject: ${outreach.message.subject}\n\n${outreach.message.body}`
        : outreach.message.body;
      navigator.clipboard.writeText(text);
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
          <h2 className="text-xl font-bold text-gray-900">Outreach Preview</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto">
          {/* Recipient Info */}
          <div className="mb-6 pb-4 border-b border-gray-200">
            <p className="text-sm text-gray-500">To:</p>
            <p className="font-medium text-gray-900">
              {contact.name}, {contact.title}
            </p>
            <p className="text-sm text-gray-500">@ {contact.company}</p>
          </div>

          {/* Channel */}
          <div className="mb-6 pb-4 border-b border-gray-200">
            <p className="text-sm text-gray-500">Channel:</p>
            <span
              className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-1 ${
                isEmail
                  ? "bg-blue-100 text-blue-700"
                  : "bg-indigo-100 text-indigo-700"
              }`}
            >
              {channel.charAt(0).toUpperCase() + channel.slice(1)}
            </span>
          </div>

          {/* Message */}
          <div className="space-y-4">
            {isEmail && outreach?.message?.subject && (
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">Subject:</p>
                <p className="text-gray-900 font-medium">
                  {outreach.message.subject}
                </p>
              </div>
            )}

            <div>
              <p className="text-sm font-medium text-gray-500 mb-1">
                {isEmail ? "Body:" : "Message:"}
              </p>
              <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-gray-700 text-sm leading-relaxed">
                {outreach?.message?.body || "No message content available."}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-end gap-3">
          <button
            onClick={handleCopy}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Copy to Clipboard
          </button>
        </div>
      </div>
    </div>
  );
}
