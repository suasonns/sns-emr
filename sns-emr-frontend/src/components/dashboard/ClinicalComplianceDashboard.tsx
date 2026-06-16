// src/components/dashboard/ClinicalComplianceDashboard.tsx

import React, { useEffect, useMemo, useState } from "react";
import {
  ClinicalComplianceDashboardResponse,
  fetchClinicalComplianceDashboard,
} from "../../api/dashboard";

const StatCard: React.FC<{ title: string; value: number }> = ({ title, value }) => {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-sm font-medium text-slate-500">{title}</div>
      <div className="mt-2 text-3xl font-semibold text-slate-900">{value}</div>
    </div>
  );
};

const SectionCard: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children,
}) => {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 text-lg font-semibold text-slate-900">{title}</div>
      {children}
    </div>
  );
};

export default function ClinicalComplianceDashboard() {
  const [data, setData] = useState<ClinicalComplianceDashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let mounted = true;

    setLoading(true);

    fetchClinicalComplianceDashboard()
      .then((payload) => {
        if (!mounted) return;
        setData(payload);
        setError("");
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "Unknown dashboard error");
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const hasData = useMemo(() => !!data, [data]);

  if (loading) {
    return <div className="p-6 text-slate-600">Loading clinical compliance dashboard...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-600">{error}</div>;
  }

  if (!hasData || !data) {
    return <div className="p-6 text-slate-600">No dashboard data available.</div>;
  }

  return (
    <div className="min-h-screen space-y-6 bg-slate-50 p-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Clinical + Compliance Dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">
          Real-time visibility into incidents, task workflow, flagged notes, and IDG blockers.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {data.metrics.map((metric) => (
          <StatCard key={metric.key} title={metric.label} value={metric.value} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <SectionCard title="Open Tasks">
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-500">
                  <th className="py-2 pr-4">Task Type</th>
                  <th className="py-2 pr-4">Patient</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Due</th>
                </tr>
              </thead>
              <tbody>
                {data.open_tasks.map((task) => (
                  <tr key={task.task_id} className="border-b last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-900">{task.task_type}</td>
                    <td className="py-2 pr-4 text-slate-700">{task.patient_id}</td>
                    <td className="py-2 pr-4 text-amber-700">{task.status}</td>
                    <td className="py-2 pr-4 text-slate-700">
                      {task.due_at ?? task.due_date ?? "—"}
                    </td>
                  </tr>
                ))}
                {data.open_tasks.length === 0 && (
                  <tr>
                    <td className="py-3 text-slate-500" colSpan={4}>
                      No open tasks.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard title="Pending Incidents">
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-500">
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Severity</th>
                  <th className="py-2 pr-4">Patient</th>
                  <th className="py-2 pr-4">Date</th>
                </tr>
              </thead>
              <tbody>
                {data.pending_incidents.map((incident) => (
                  <tr key={incident.incident_id} className="border-b last:border-0">
                    <td className="py-2 pr-4 font-medium text-slate-900">{incident.incident_type}</td>
                    <td className="py-2 pr-4 text-rose-700">{incident.incident_severity}</td>
                    <td className="py-2 pr-4 text-slate-700">{incident.patient_id}</td>
                    <td className="py-2 pr-4 text-slate-700">{incident.incident_date ?? "—"}</td>
                  </tr>
                ))}
                {data.pending_incidents.length === 0 && (
                  <tr>
                    <td className="py-3 text-slate-500" colSpan={4}>
                      No pending incidents.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <SectionCard title="Flagged Notes">
          <div className="space-y-3">
            {data.flagged_notes.map((note) => (
              <div key={note.note_id} className="rounded-xl border border-slate-200 p-3">
                <div className="text-sm font-semibold text-slate-900">
                  Patient {note.patient_id} · {note.discipline ?? "—"} · {note.visit_type ?? "—"}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Note {note.note_id} · {note.encounter_date ?? "—"} · {note.note_category ?? "—"}
                </div>

                {note.red_flags.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs font-semibold uppercase tracking-wide text-rose-700">
                      Red Flags
                    </div>
                    <ul className="mt-1 list-disc pl-5 text-sm text-rose-700">
                      {note.red_flags.map((flag) => (
                        <li key={flag}>{flag}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {note.needs_clarification.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                      Needs Clarification
                    </div>
                    <ul className="mt-1 list-disc pl-5 text-sm text-amber-700">
                      {note.needs_clarification.map((flag) => (
                        <li key={flag}>{flag}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}

            {data.flagged_notes.length === 0 && (
              <div className="text-sm text-slate-500">No flagged notes.</div>
            )}
          </div>
        </SectionCard>

        <SectionCard title="IDG Blocked Patients">
          <div className="space-y-3">
            {data.blocked_patients.map((patient) => (
              <div key={patient.patient_id} className="rounded-xl border border-slate-200 p-3">
                <div className="text-sm font-semibold text-slate-900">
                  Patient {patient.patient_id}
                </div>
                <ul className="mt-2 list-disc pl-5 text-sm text-amber-700">
                  {patient.blockers.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            ))}

            {data.blocked_patients.length === 0 && (
              <div className="text-sm text-slate-500">No IDG blockers.</div>
            )}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}