"use client";

import { useState, Fragment } from "react";
import { addEvents } from "@/lib/api";

const EMPTY_ROWS = () => Array.from({ length: 10 }, () => ({ event_name: "", event_url: "" }));

export default function AddEventsModal() {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState(EMPTY_ROWS);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const updateRow = (i: number, field: "event_name" | "event_url", value: string) => {
    const next = [...rows];
    next[i] = { ...next[i], [field]: value };
    setRows(next);
  };

  const handleSubmit = async () => {
    const valid = rows.filter((r) => r.event_name.trim() && r.event_url.trim());
    if (!valid.length) return;

    setLoading(true);
    setResult(null);
    try {
      const res = await addEvents(valid);
      setResult(`Added ${res.added} event(s), ${res.scored} scored.`);
      setRows(EMPTY_ROWS());
    } catch (e: unknown) {
      setResult(`Error: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="px-4 py-2 bg-neutral-950 text-white text-xs font-medium rounded-md hover:bg-neutral-800 transition-colors"
      >
        + Add Events
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => !loading && setOpen(false)}>
          <div className="bg-white rounded-lg border border-neutral-200 shadow-2xl p-6 w-full max-w-2xl max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-neutral-950 mb-4">Add Events</h3>
            <div className="grid grid-cols-[1fr_1fr] gap-x-3 gap-y-2">
              <span className="text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">Event Name</span>
              <span className="text-[10px] font-medium text-neutral-500 mb-1 uppercase tracking-wide">Event URL</span>
              {rows.map((row, i) => (
                <Fragment key={i}>
                  <input
                    type="text"
                    placeholder={`Event ${i + 1}`}
                    value={row.event_name}
                    onChange={(e) => updateRow(i, "event_name", e.target.value)}
                    className="px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="https://..."
                    value={row.event_url}
                    onChange={(e) => updateRow(i, "event_url", e.target.value)}
                    className="px-3 py-2 border border-neutral-200 rounded-md text-sm text-neutral-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </Fragment>
              ))}
            </div>
            <div className="flex items-center justify-end gap-3 mt-4">
              <button onClick={() => setOpen(false)} disabled={loading} className="text-xs text-neutral-500 hover:text-neutral-700">
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-4 py-2 bg-neutral-950 text-white text-xs font-medium rounded-md hover:bg-neutral-800 disabled:opacity-50 transition-colors"
              >
                {loading ? "Enriching & Scoring..." : "Confirm"}
              </button>
            </div>
            {result && (
              <p className={`mt-3 text-xs ${result.startsWith("Error") ? "text-red-600" : "text-emerald-600"}`}>
                {result}
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
