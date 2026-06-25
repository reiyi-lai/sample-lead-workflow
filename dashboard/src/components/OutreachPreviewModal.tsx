"use client";

import { ContactWithOutreach } from "@/lib/data";
import { X, Copy } from "lucide-react";

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
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative bg-white rounded-lg border border-neutral-200 shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200">
          <h2 className="text-base font-semibold text-neutral-950">Outreach Preview</h2>
          <button
            onClick={onClose}
            className="text-neutral-500 hover:text-neutral-700 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-6 py-5 overflow-y-auto">
          <div className="mb-5 pb-4 border-b border-neutral-100">
            <p className="text-[10px] text-neutral-500 uppercase tracking-wide">To</p>
            <p className="text-sm font-medium text-neutral-950 mt-0.5">
              {contact.name}, {contact.title}
            </p>
            <p className="text-xs text-neutral-500">{contact.company}</p>
          </div>

          <div className="mb-5 pb-4 border-b border-neutral-100">
            <p className="text-[10px] text-neutral-500 uppercase tracking-wide">Channel</p>
            <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wide mt-1 border border-neutral-200 text-neutral-500">
              {channel.charAt(0).toUpperCase() + channel.slice(1)}
            </span>
          </div>

          <div className="space-y-4">
            {isEmail && outreach?.message?.subject && (
              <div>
                <p className="text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">Subject</p>
                <p className="text-sm text-neutral-950 font-medium">{outreach.message.subject}</p>
              </div>
            )}

            <div>
              <p className="text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">
                {isEmail ? "Body" : "Message"}
              </p>
              <div className="border border-neutral-200 rounded-md p-4 whitespace-pre-wrap text-sm text-neutral-700 leading-relaxed">
                {outreach?.message?.body || "No message content available."}
              </div>
            </div>
          </div>
        </div>

        <div className="px-6 py-3 border-t border-neutral-200 flex items-center justify-end">
          <button
            onClick={handleCopy}
            className="px-4 py-2 text-xs font-medium text-white bg-neutral-950 rounded-md hover:bg-neutral-800 transition-colors inline-flex items-center gap-1.5"
          >
            <Copy size={12} />
            Copy
          </button>
        </div>
      </div>
    </div>
  );
}
