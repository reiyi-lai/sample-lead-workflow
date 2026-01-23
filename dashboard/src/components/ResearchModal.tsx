"use client";

import { CompanyWithDetails } from "@/lib/data";

interface ResearchModalProps {
  company: CompanyWithDetails;
  onClose: () => void;
}

export default function ResearchModal({ company, onClose }: ResearchModalProps) {
  const research = company.research;

  if (!research) return null;

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
            Research
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
          {research.business_overview && (
            <Section title="Business Overview" content={research.business_overview} />
          )}

          {research.products_and_positioning && (
            <Section
              title="Products & Positioning"
              content={research.products_and_positioning}
            />
          )}

          {research.strategic_relevance_to_tedlar && (
            <Section
              title="Strategic Relevance to Tedlar"
              content={research.strategic_relevance_to_tedlar}
            />
          )}

          {research.potential_pain_points && (
            <Section
              title="Potential Pain Points"
              content={research.potential_pain_points}
            />
          )}

          {research.market_activity && (
            <Section title="Market Activity" content={research.market_activity} />
          )}

          {research.company_scale && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-2">
                Company Scale
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm text-gray-600">
                {research.company_scale.estimated_revenue && (
                  <p>
                    <span className="font-medium">Revenue:</span>{" "}
                    {research.company_scale.estimated_revenue}
                  </p>
                )}
                {research.company_scale.estimated_employees && (
                  <p>
                    <span className="font-medium">Employees:</span>{" "}
                    {research.company_scale.estimated_employees}
                  </p>
                )}
                {research.company_scale.scale_synthesis && (
                  <p className="mt-2">{research.company_scale.scale_synthesis}</p>
                )}
              </div>
            </div>
          )}

          {research.additional_insights && (
            <Section
              title="Additional Insights"
              content={research.additional_insights}
            />
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

function Section({ title, content }: { title: string; content: string }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
        {content}
      </p>
    </div>
  );
}
