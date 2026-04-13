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
        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
      >
        + Add Events
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => !loading && setOpen(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-gray-900 mb-4 text-lg">Add Events</h3>
            <div className="grid grid-cols-[1fr_1fr] gap-x-3 gap-y-2">
              <span className="text-xs font-medium text-gray-500 mb-1">Event Name</span>
              <span className="text-xs font-medium text-gray-500 mb-1">Event URL</span>
              {rows.map((row, i) => (
                <Fragment key={i}>
                  <input
                    type="text"
                    placeholder={`Event ${i + 1}`}
                    value={row.event_name}
                    onChange={(e) => updateRow(i, "event_name", e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900"
                  />
                  <input
                    type="text"
                    placeholder="https://..."
                    value={row.event_url}
                    onChange={(e) => updateRow(i, "event_url", e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900"
                  />
                </Fragment>
              ))}
            </div>
            <div className="flex items-center justify-end gap-3 mt-4">
              <button onClick={() => setOpen(false)} disabled={loading} className="text-sm text-gray-600 hover:text-gray-800">
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Enriching & Scoring..." : "Confirm"}
              </button>
            </div>
            {result && (
              <p className={`mt-3 text-sm ${result.startsWith("Error") ? "text-red-600" : "text-green-600"}`}>
                {result}
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
