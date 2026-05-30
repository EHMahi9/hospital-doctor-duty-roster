import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { analyticsApi } from "@/api/endpoints";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { BalanceLedger } from "@/types/api";

export function AnalyticsPage() {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [rows, setRows] = useState<BalanceLedger[]>([]);

  useEffect(() => {
    analyticsApi
      .balanceLedger(month, year)
      .then(setRows)
      .catch((error) => toast.error(errorMessage(error)));
  }, [month, year]);

  const topWorkloads = useMemo(
    () =>
      rows
        .slice()
        .sort((a, b) => b.workload_score - a.workload_score)
        .slice(0, 12)
        .map((row) => ({ ...row, name: row.doctor_name.replace("Dr. ", "") })),
    [rows]
  );

  return (
    <div>
      <PageHeader
        eyebrow="Roster Intelligence"
        title="Balance Ledger and Workload Analytics"
        actions={
          <>
            <Input className="w-24" type="number" min={1} max={12} value={month} onChange={(event) => setMonth(Number(event.target.value))} />
            <Input className="w-28" type="number" min={2020} value={year} onChange={(event) => setYear(Number(event.target.value))} />
          </>
        }
      />

      <section className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Workload Score</CardTitle>
          </CardHeader>
          <CardContent className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topWorkloads}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={82} />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: "#0f1f2c", border: "1px solid rgba(148,163,184,0.24)", borderRadius: 8 }} />
                <Bar dataKey="workload_score" fill="#14b8a6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Fairness Score</CardTitle>
          </CardHeader>
          <CardContent className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={topWorkloads}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" />
                <XAxis dataKey="name" stroke="#94a3b8" hide />
                <YAxis stroke="#94a3b8" domain={[0, 100]} />
                <Tooltip contentStyle={{ background: "#0f1f2c", border: "1px solid rgba(148,163,184,0.24)", borderRadius: 8 }} />
                <Line type="monotone" dataKey="fairness_score" stroke="#f59e0b" strokeWidth={3} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </section>

      <section className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Balance Ledger</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[980px] text-sm">
                <thead className="text-left text-muted-foreground">
                  <tr>
                    <th className="border-b p-3 font-medium">Doctor</th>
                    <th className="border-b p-3 font-medium">Emergency</th>
                    <th className="border-b p-3 font-medium">Indoor</th>
                    <th className="border-b p-3 font-medium">Outdoor</th>
                    <th className="border-b p-3 font-medium">Night</th>
                    <th className="border-b p-3 font-medium">Total</th>
                    <th className="border-b p-3 font-medium">Extra</th>
                    <th className="border-b p-3 font-medium">Missed</th>
                    <th className="border-b p-3 font-medium">Overtime</th>
                    <th className="border-b p-3 font-medium">Fairness</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.doctor_id} className="hover:bg-secondary/40">
                      <td className="border-b p-3 font-semibold">{row.doctor_name}</td>
                      <td className="border-b p-3">{row.emergency_count}</td>
                      <td className="border-b p-3">{row.indoor_count}</td>
                      <td className="border-b p-3">{row.outdoor_count}</td>
                      <td className="border-b p-3">{row.night_count}</td>
                      <td className="border-b p-3">{row.total_duties}</td>
                      <td className="border-b p-3">
                        <Badge variant={row.extra_duties > 0 ? "warning" : "secondary"}>{row.extra_duties}</Badge>
                      </td>
                      <td className="border-b p-3">{row.missed_duties}</td>
                      <td className="border-b p-3">{row.overtime_hours}</td>
                      <td className="border-b p-3">{row.fairness_score}</td>
                    </tr>
                  ))}
                  {!rows.length ? (
                    <tr>
                      <td className="p-8 text-center text-muted-foreground" colSpan={10}>
                        No ledger rows for this month
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
