type SummaryItem = {
  label: string;
  value: any;
};

type EligibilitySummary = {
  summary_type: string;

  functional_status: SummaryItem[];
  disease_progression: SummaryItem[];
  nutrition: SummaryItem[];
  safety: SummaryItem[];
  caregiver_support: SummaryItem[];
  communication: SummaryItem[];
};

interface Props {
  summary: EligibilitySummary | null;
}

function renderValue(value: any): string {
  if (value === null || value === undefined) {
    return "Not Documented";
  }

  if (value === true) {
    return "Yes";
  }

  if (value === false) {
    return "No";
  }

  return String(value);
}

function Section({
  title,
  items,
}: {
  title: string;
  items: SummaryItem[];
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-600">
        {title}
      </h3>

      <div className="space-y-2">
        {items.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between border-b border-slate-100 pb-2"
          >
            <span className="text-sm text-slate-700">
              {item.label}
            </span>

            <span className="font-medium text-slate-900">
              {renderValue(item.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function EligibilityEvidenceSummaryPanel({
  summary,
}: Props) {
  if (!summary) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold">
          Eligibility Evidence Summary
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          No eligibility evidence available.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <h2 className="text-lg font-semibold text-blue-900">
          Eligibility Evidence Summary
        </h2>

        <p className="mt-1 text-sm text-blue-700">
          Harvested evidence from RN ICA. Read-only summary.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Section
          title="Functional Status"
          items={summary.functional_status}
        />

        <Section
          title="Disease Progression"
          items={summary.disease_progression}
        />

        <Section
          title="Nutrition"
          items={summary.nutrition}
        />

        <Section
          title="Safety"
          items={summary.safety}
        />

        <Section
          title="Caregiver Support"
          items={summary.caregiver_support}
        />

        <Section
          title="Communication"
          items={summary.communication}
        />
      </div>
    </div>
  );
}