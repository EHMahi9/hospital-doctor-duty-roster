import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { Check, Send, X } from "lucide-react";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { doctorApi, leaveApi } from "@/api/endpoints";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { Doctor, LeaveRequest, LeaveStatus, LeaveType } from "@/types/api";

export function LeavesPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState<LeaveStatus | "">("");
  const [form, setForm] = useState({
    doctor_id: 0,
    leave_date: new Date().toISOString().slice(0, 10),
    leave_type: "casual" as LeaveType,
    reason: ""
  });

  const load = useCallback(async () => {
    try {
      const [doctorRows, leaveRows] = await Promise.all([
        doctorApi.list({ is_active: true }),
        leaveApi.list({ status: statusFilter || undefined })
      ]);
      setDoctors(doctorRows);
      setLeaves(leaveRows);
      if (!form.doctor_id && doctorRows[0]) {
        setForm((current) => ({ ...current, doctor_id: doctorRows[0].id }));
      }
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }, [form.doctor_id, statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const events = useMemo(
    () =>
      leaves.map((leave) => ({
        id: String(leave.id),
        title: `${leave.doctor.name} - ${leave.status}`,
        start: leave.leave_date,
        backgroundColor: leave.status === "approved" ? "#14b8a6" : leave.status === "rejected" ? "#ef4444" : "#f59e0b",
        borderColor: "transparent"
      })),
    [leaves]
  );

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await leaveApi.apply(form);
      toast.success("Leave request submitted");
      setForm((current) => ({ ...current, reason: "" }));
      load();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  async function decide(id: number, status: "approved" | "rejected") {
    try {
      await leaveApi.decide(id, status);
      toast.success(`Leave ${status}`);
      load();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Leave Management"
        title="Leave Applications and Calendar"
        actions={
          <Select className="w-44" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as LeaveStatus | "")}>
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </Select>
        }
      />

      <section className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Apply Leave</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submit}>
                <div className="space-y-2">
                  <Label>Doctor</Label>
                  <Select value={form.doctor_id} onChange={(event) => setForm({ ...form, doctor_id: Number(event.target.value) })}>
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
                    <Input type="date" value={form.leave_date} onChange={(event) => setForm({ ...form, leave_date: event.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Type</Label>
                    <Select value={form.leave_type} onChange={(event) => setForm({ ...form, leave_type: event.target.value as LeaveType })}>
                      <option value="casual">Casual</option>
                      <option value="sick">Sick</option>
                      <option value="earned">Earned</option>
                      <option value="training">Training</option>
                      <option value="other">Other</option>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Reason</Label>
                  <Textarea value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} required />
                </div>
                <Button className="w-full">
                  <Send className="h-4 w-4" />
                  Submit leave
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Approval Queue</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {leaves.map((leave) => (
                <div key={leave.id} className="rounded-md border bg-background/70 p-3">
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{leave.doctor.name}</p>
                      <p className="text-xs text-muted-foreground">{leave.leave_date}</p>
                    </div>
                    <Badge variant={leave.status === "approved" ? "default" : leave.status === "rejected" ? "destructive" : "warning"}>
                      {leave.status}
                    </Badge>
                  </div>
                  <p className="mb-3 text-sm text-muted-foreground">{leave.reason}</p>
                  {leave.status === "pending" ? (
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => decide(leave.id, "approved")}>
                        <Check className="h-3.5 w-3.5" />
                        Approve
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => decide(leave.id, "rejected")}>
                        <X className="h-3.5 w-3.5" />
                        Reject
                      </Button>
                    </div>
                  ) : null}
                </div>
              ))}
              {!leaves.length ? <p className="py-6 text-center text-sm text-muted-foreground">No leave requests found</p> : null}
            </CardContent>
          </Card>
        </div>

        <Card className="print-surface">
          <CardHeader>
            <CardTitle>Leave Calendar</CardTitle>
          </CardHeader>
          <CardContent>
            <FullCalendar
              plugins={[dayGridPlugin, interactionPlugin]}
              initialView="dayGridMonth"
              height="auto"
              events={events}
              headerToolbar={{ left: "prev,next today", center: "title", right: "dayGridMonth" }}
            />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
