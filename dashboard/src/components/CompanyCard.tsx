"use client";

import { useState } from "react";
import { CompanyWithDetails } from "@/lib/data";
import TargetRolesModal from "./TargetRolesModal";
import Link from "next/link";

interface CompanyCardProps {
  company: CompanyWithDetails;
}

export default function CompanyCard({ company }: CompanyCardProps) {
  const [showRoles, setShowRoles] = useState(false);

  const draftCount = company.contacts.filter(
    (c) => c.outreach && (!c.outreach.status || c.outreach.status === "draft")
  ).length;

  return (
    <>
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold text-gray-900">{company.name}</h3>
          <div className="text-right">
            <span className="text-2xl font-bold text-gray-900">
              {company.score > 0 ? Math.round(company.score) : "—"}
            </span>
            {company.score > 0 && (
              <span className="text-sm text-gray-500 ml-1">/100</span>
            )}
          </div>
        </div>

        {/* Event & Website */}
        <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
          <span>{company.event}</span>
          {company.scoring?.website_url && (
            <>
              <span>•</span>
              <a
                href={company.scoring.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline truncate"
              >
                {company.scoring.website_url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
              </a>
            </>
          )}
        </div>

        {/* Score Breakdown */}
        {company.scoring?.scores && (
          <div className="mt-4 bg-gray-50 rounded-lg p-4 space-y-3">
            {company.scoring.scores.industry_fit && (
              <ScoreRow
                label="Industry Fit"
                score={company.scoring.scores.industry_fit.score}
                rationale={company.scoring.scores.industry_fit.rationale}
              />
            )}
            {company.scoring.scores.size_revenue_fit && (
              <ScoreRow
                label="Size/Revenue"
                score={company.scoring.scores.size_revenue_fit.score}
                rationale={company.scoring.scores.size_revenue_fit.rationale}
              />
            )}
            {company.scoring.scores.strategic_relevance && (
              <ScoreRow
                label="Strategic Relevance"
                score={company.scoring.scores.strategic_relevance.score}
                rationale={company.scoring.scores.strategic_relevance.rationale}
              />
            )}
            {company.scoring.scores.market_activity && (
              <ScoreRow
                label="Market Activity"
                score={company.scoring.scores.market_activity.score}
                rationale={company.scoring.scores.market_activity.rationale}
              />
            )}
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
          <span>👥 {company.contacts.length} contacts</span>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-100 mt-4 pt-4">
          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowRoles(true)}
              disabled={!company.targetRoles}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                company.targetRoles
                  ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  : "bg-gray-50 text-gray-400 cursor-not-allowed"
              }`}
            >
              Target Roles
            </button>
            {company.contacts.length > 0 && (
              <Link
                href={`/outreach?company=${encodeURIComponent(company.name)}`}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors ml-auto"
              >
                View Outreach →
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showRoles && company.targetRoles && (
        <TargetRolesModal
          company={company}
          onClose={() => setShowRoles(false)}
        />
      )}
    </>
  );
}

function ScoreRow({
  label,
  score,
  rationale,
}: {
  label: string;
  score: number;
  rationale: string;
}) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-green-600";
    if (score >= 6) return "text-yellow-600";
    return "text-gray-600";
  };

  return (
    <div className="flex items-start gap-4">
      <div className="flex items-center gap-2 min-w-[180px] shrink-0">
        <span className={`font-semibold ${getScoreColor(score)} w-[45px]`}>
          {score}/10
        </span>
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <p className="text-sm text-gray-600 leading-relaxed">
        {rationale}
      </p>
    </div>
  );
}
