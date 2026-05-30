import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { format } from "date-fns";
import { Download, FileSpreadsheet, Printer, RefreshCw, Save } from "lucide-react";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { doctorApi, rosterApi } from "@/api/endpoints";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { downloadBlob, formatMonth } from "@/lib/utils";
import type { Doctor, DutyAssignment, DutyType, MonthlySummary, RosterConflict } from "@/types/api";

const dutyTypes: DutyType[] = [
  "Emergency Morning",
  "Emergency Evening",
  "Emergency Night",
  "Indoor Morning",
  "Indoor Night",
  "Outdoor"
];

const dutyColors: Record<DutyType, string> = {
  "Emergency Morning": "#ef4444",
  "Emergency Evening": "#f97316",
  "Emergency Night": "#be123c",
  "Indoor Morning": "#14b8a6",
  "Indoor Night": "#0ea5e9",
  Outdoor: "#f59e0b"
};

export function RosterPage() {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [assignments, setAssignments] = useState<DutyAssignment[]>([]);
  const [conflicts, setConflicts] = useState<RosterConflict[]>([]);
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorFilter, setDoctorFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [generating, setGenerating] = useState(false);
  const [manual, setManual] = useState({
    doctor_id: 0,
    duty_date: today.toISOString().slice(0, 10),
    duty_type: "Emergency Morning" as DutyType,
    notes: ""
  });

  const load = useCallback(async () => {
    try {
      const [assignmentRows, conflictRows, summaryRow, doctorRows] = await Promise.all([
        rosterApi.list(month, year, {
          doctor_id: doctorFilter ? Number(doctorFilter) : undefined,
          department_id: departmentFilter ? Number(departmentFilter) : undefined
        }),
        rosterApi.conflicts(month, year),
        rosterApi.summary(month, year),
        doctorApi.list({ is_active: true })
      ]);
      setAssignments(assignmentRows);
      setConflicts(conflictRows);
      setSummary(summaryRow);
      setDoctors(doctorRows);
      if (!manual.doctor_id && doctorRows[0]) {
        setManual((current) => ({ ...current, doctor_id: doctorRows[0].id }));
      }
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }, [departmentFilter, doctorFilter, manual.doctor_id, month, year]);

  useEffect(() => {
    load();
  }, [load]);

  const generate = useCallback(async () => {
    setGenerating(true);
    try {
      const result = await rosterApi.generate({
        month,
        year,
        overwrite: true,
        preserve_manual_overrides: true,
        seed: Number(`${year}${String(month).padStart(2, "0")}`)
      });
      toast.success(`Generated ${result.assignments_created} duty assignments`);
      if (result.conflicts.length) {
        toast.warning(`${result.conflicts.length} roster conflicts need review`);
      }
      load();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setGenerating(false);
    }
  }, [load, month, year]);

  useKeyboardShortcuts({
    "Ctrl+G": generate
  });

  const eventData = useMemo(
    () =>
      assignments.map((assignment) => {
        const conflict = conflicts.some(
          (item) => item.duty_date === assignment.duty_date && (!item.duty_type || item.duty_type === assignment.duty_type)
        );
        return {
          id: String(assignment.id),
          title: `${assignment.duty_type}: ${assignment.doctor.name}`,
          start: assignment.duty_date,
          backgroundColor: dutyColors[assignment.duty_type],
          borderColor: "transparent",
          classNames: conflict ? ["roster-conflict"] : [],
          extendedProps: {
            doctor_id: assignment.doctor_id,
            duty_type: assignment.duty_type
          }
        };
      }),
    [assignments, conflicts]
  );

  async function submitManual(event: FormEvent) {
    event.preventDefault();
    try {
      await rosterApi.manualOverride({ ...manual, force: true });
      toast.success("Manual override saved");
      load();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  async function exportRoster(type: "xlsx" | "pdf") {
    try {
      const blob = await rosterApi.exportFile(month, year, type);
      downloadBlob(blob, `hospital-roster-${year}-${String(month).padStart(2, "0")}.${type}`);
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Monthly Roster Generator"
        title={formatMonth(month, year)}
        actions={
          <>
            <Input className="w-24" type="number" min={1} max={12} value={month} onChange={(event) => setMonth(Number(event.target.value))} />
            <Input className="w-28" type="number" min={2020} value={year} onChange={(event) => setYear(Number(event.target.value))} />
            <Button onClick={generate} disabled={generating}>
              <RefreshCw className="h-4 w-4" />
              {generating ? "Generating" : "Generate"}
            </Button>
            <Button variant="secondary" onClick={() => exportRoster("xlsx")}>
              <FileSpreadsheet className="h-4 w-4" />
              Excel
            </Button>
            <Button variant="secondary" onClick={() => exportRoster("pdf")}>
              <Download className="h-4 w-4" />
              PDF
            </Button>
            <Button variant="outline" onClick={() => window.print()}>
              <Printer className="h-4 w-4" />
              Print
            </Button>
          </>
        }
      />

      <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total duties</p>
            <p className="mt-1 text-2xl font-bold">{summary?.total_duties ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Emergency</p>
            <p className="mt-1 text-2xl font-bold">{summary?.emergency_duties ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Indoor</p>
            <p className="mt-1 text-2xl font-bold">{summary?.indoor_duties ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Outdoor</p>
            <p className="mt-1 text-2xl font-bold">{summary?.outdoor_duties ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Overtime hours</p>
            <p className="mt-1 text-2xl font-bold">{summary?.overtime_hours ?? 0}</p>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 2xl:grid-cols-[1fr_420px]">
        <Card className="print-surface min-w-0">
          <CardHeader>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <CardTitle>Scheduler</CardTitle>
              <div className="no-print flex flex-col gap-2 sm:flex-row">
                <Select className="w-56" value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)}>
                  <option value="">All departments</option>
                  {Array.from(new Map(doctors.map((doctor) => [doctor.department.id, doctor.department])).values()).map((department) => (
                    <option key={department.id} value={department.id}>
                      {department.name}
                    </option>
                  ))}
                </Select>
                <Select className="w-56" value={doctorFilter} onChange={(event) => setDoctorFilter(event.target.value)}>
                  <option value="">All doctors</option>
                  {doctors.map((doctor) => (
                    <option key={doctor.id} value={doctor.id}>
                      {doctor.name}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <FullCalendar
              key={`${year}-${month}`}
              plugins={[dayGridPlugin, interactionPlugin]}
              initialView="dayGridMonth"
              initialDate={`${year}-${String(month).padStart(2, "0")}-01`}
              height="auto"
              editable
              events={eventData}
              headerToolbar={{ left: "prev,next today", center: "title", right: "dayGridMonth" }}
              eventDrop={async (info) => {
                const dutyType = info.event.extendedProps.duty_type as DutyType;
                const doctorId = Number(info.event.extendedProps.doctor_id);
                const dutyDate = info.event.start ? format(info.event.start, "yyyy-MM-dd") : "";
                try {
                  await rosterApi.manualOverride({ doctor_id: doctorId, duty_date: dutyDate, duty_type: dutyType, force: true });
                  toast.success("Roster updated");
                  load();
                } catch (error) {
                  info.revert();
                  toast.error(errorMessage(error));
                }
              }}
            />
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Manual Override</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submitManual}>
                <div className="space-y-2">
                  <Label>Doctor</Label>
                  <Select value={manual.doctor_id} onChange={(event) => setManual({ ...manual, doctor_id: Number(event.target.value) })}>
                    {doctors.map((doctor) => (
                      <option key={doctor.id} value={doctor.id}>
                        {doctor.name}
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Date</Label>
                    <Input type="date" value={manual.duty_date} onChange={(event) => setManual({ ...manual, duty_date: event.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Duty</Label>
                    <Select value={manual.duty_type} onChange={(event) => setManual({ ...manual, duty_type: event.target.value as DutyType })}>
                      {dutyTypes.map((dutyType) => (
                        <option key={dutyType} value={dutyType}>
                          {dutyType}
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea value={manual.notes} onChange={(event) => setManual({ ...manual, notes: event.target.value })} />
                </div>
                <Button className="w-full">
                  <Save className="h-4 w-4" />
                  Save override
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Conflict Monitor</CardTitle>
            </CardHeader>
            <CardContent className="max-h-[420px] space-y-3 overflow-y-auto">
              {conflicts.map((conflict, index) => (
                <div key={`${conflict.code}-${index}`} className="rounded-md border bg-background/70 p-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <Badge variant={conflict.severity === "high" ? "destructive" : "warning"}>{conflict.code}</Badge>
                    <span className="text-xs text-muted-foreground">{conflict.duty_date}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{conflict.message}</p>
                </div>
              ))}
              {!conflicts.length ? <p className="py-6 text-center text-sm text-muted-foreground">No conflicts detected</p> : null}
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Monthly Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px] text-sm">
                <thead className="text-left text-muted-foreground">
                  <tr>
                    <th className="border-b p-3 font-medium">Doctor</th>
                    <th className="border-b p-3 font-medium">Department</th>
                    <th className="border-b p-3 font-medium">Emergency</th>
                    <th className="border-b p-3 font-medium">Indoor</th>
                    <th className="border-b p-3 font-medium">Outdoor</th>
                    <th className="border-b p-3 font-medium">Night</th>
                    <th className="border-b p-3 font-medium">Total</th>
                    <th className="border-b p-3 font-medium">Fairness</th>
                  </tr>
                </thead>
                <tbody>
                  {(summary?.by_doctor ?? []).map((row) => (
                    <tr key={String(row.doctor_id)} className="hover:bg-secondary/40">
                      <td className="border-b p-3 font-semibold">{row.doctor_name}</td>
                      <td className="border-b p-3">{row.department}</td>
                      <td className="border-b p-3">{row.emergency}</td>
                      <td className="border-b p-3">{row.indoor}</td>
                      <td className="border-b p-3">{row.outdoor}</td>
                      <td className="border-b p-3">{row.night}</td>
                      <td className="border-b p-3">{row.total}</td>
                      <td className="border-b p-3">{row.fairness_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
