"use client";

import { useState } from "react";
import { CompanyWithDetails } from "@/lib/data";
import TargetRolesModal from "./TargetRolesModal";
import Link from "next/link";
import { ArrowRight, ExternalLink } from "lucide-react";

interface CompanyCardProps {
  company: CompanyWithDetails;
}

export default function CompanyCard({ company }: CompanyCardProps) {
  const [showRoles, setShowRoles] = useState(false);

  return (
    <>
      <div className="border border-neutral-200 rounded-2xl p-5 hover:border-neutral-300 transition-colors">
        <div className="flex items-start justify-between">
          <h3 className="text-base font-semibold text-neutral-950">{company.name}</h3>
          <div className="text-right">
            <span className="text-2xl font-semibold text-neutral-950 tracking-tight">
              {company.score > 0 ? Math.round(company.score) : "—"}
            </span>
            {company.score > 0 && (
              <span className="text-xs text-neutral-500 ml-1">/100</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 mt-1.5 text-xs text-neutral-500">
          <span>{company.event}</span>
          {company.scoring?.website_url && (
            <>
              <span>·</span>
              <a
                href={company.scoring.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-neutral-500 hover:text-neutral-950 inline-flex items-center gap-1"
              >
                {company.scoring.website_url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
                <ExternalLink size={10} />
              </a>
            </>
          )}
        </div>

        {company.scoring?.scores && (
          <div className="mt-4 border border-neutral-100 rounded-lg p-4 space-y-2.5">
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

        <div className="flex items-center gap-4 mt-4 text-xs text-neutral-500">
          <span>{company.contacts.length} contacts</span>
        </div>

        <div className="border-t border-neutral-100 mt-4 pt-4">
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setShowRoles(true)}
              disabled={!company.targetRoles}
              className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-colors ${
                company.targetRoles
                  ? "border border-neutral-200 text-neutral-700 hover:bg-neutral-100"
                  : "border border-neutral-100 text-neutral-300 cursor-not-allowed"
              }`}
            >
              Target Roles
            </button>
            {company.contacts.length > 0 && (
              <Link
                href={`/outreach?company=${encodeURIComponent(company.name)}`}
                className="px-3.5 py-1.5 text-xs font-medium rounded-md bg-neutral-950 text-white hover:bg-neutral-800 transition-colors ml-auto inline-flex items-center gap-1.5"
              >
                View Outreach
                <ArrowRight size={12} />
              </Link>
            )}
          </div>
        </div>
      </div>

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
  return (
    <div className="flex items-start gap-4">
      <div className="flex items-center gap-2 min-w-[170px] shrink-0">
        <span className={`font-semibold text-sm w-[42px] ${
          score >= 8 ? "text-emerald-700" : score >= 6 ? "text-amber-600" : "text-red-500"
        }`}>
          {score}/10
        </span>
        <span className="text-xs text-neutral-500">{label}</span>
      </div>
      <p className="text-xs text-neutral-500 leading-relaxed">{rationale}</p>
    </div>
  );
}
