import { useEffect, useMemo, useState } from "react";
import { Activity, CalendarCheck, Clock3, DoorOpen, Siren, Stethoscope } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import { analyticsApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { MetricCard } from "@/components/layout/MetricCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { DashboardOverview } from "@/types/api";

const colors = ["#14b8a6", "#f59e0b", "#38bdf8", "#fb7185"];

export function DashboardPage() {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    analyticsApi
      .overview(month, year)
      .then(setOverview)
      .catch((error) => toast.error(errorMessage(error)))
      .finally(() => setLoading(false));
  }, [month, year]);

  const workloadData = useMemo(
    () =>
      (overview?.workload_analytics ?? []).slice(0, 10).map((row) => ({
        name: String(row.doctor_name ?? ""),
        duties: Number(row.total ?? 0),
        workload: Number(row.weighted_workload ?? 0),
        fairness: Number(row.fairness_score ?? 0)
      })),
    [overview]
  );

  return (
    <div>
      <PageHeader
        eyebrow="Command Center"
        title="Hospital Duty Dashboard"
        actions={
          <>
            <Input className="w-28" type="number" min={1} max={12} value={month} onChange={(event) => setMonth(Number(event.target.value))} />
            <Input className="w-32" type="number" min={2020} value={year} onChange={(event) => setYear(Number(event.target.value))} />
          </>
        }
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <MetricCard label="Total doctors" value={overview?.total_doctors ?? (loading ? "..." : 0)} icon={Stethoscope} />
        <MetricCard label="Total duties" value={overview?.total_duties ?? (loading ? "..." : 0)} icon={CalendarCheck} tone="blue" />
        <MetricCard label="Emergency" value={overview?.emergency_duty_count ?? (loading ? "..." : 0)} icon={Siren} tone="rose" />
        <MetricCard label="Indoor" value={overview?.indoor_duty_count ?? (loading ? "..." : 0)} icon={DoorOpen} tone="amber" />
        <MetricCard label="Outdoor" value={overview?.outdoor_duty_count ?? (loading ? "..." : 0)} icon={Activity} />
        <MetricCard label="Upcoming leaves" value={overview?.upcoming_leaves ?? (loading ? "..." : 0)} icon={Clock3} tone="amber" />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Workload Analytics</CardTitle>
          </CardHeader>
          <CardContent className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={workloadData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={82} />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: "#0f1f2c", border: "1px solid rgba(148,163,184,0.24)", borderRadius: 8 }} />
                <Bar dataKey="duties" fill="#14b8a6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="workload" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Duty Mix</CardTitle>
          </CardHeader>
          <CardContent className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={overview?.duty_mix ?? []} dataKey="value" nameKey="name" innerRadius={72} outerRadius={118} paddingAngle={2}>
                  {(overview?.duty_mix ?? []).map((entry, index) => (
                    <Cell key={entry.name} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0f1f2c", border: "1px solid rgba(148,163,184,0.24)", borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </section>

      <section className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Fairness Trend Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={workloadData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" />
                <XAxis dataKey="name" stroke="#94a3b8" hide />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: "#0f1f2c", border: "1px solid rgba(148,163,184,0.24)", borderRadius: 8 }} />
                <Area type="monotone" dataKey="fairness" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.18} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
