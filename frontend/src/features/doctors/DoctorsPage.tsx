import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, Pencil, Plus, Search, Trash2, XCircle } from "lucide-react";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { doctorApi } from "@/api/endpoints";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import type { Department, Doctor, PreferredShift } from "@/types/api";

const emptyForm = {
  name: "",
  email: "",
  phone: "",
  department_id: 0,
  designation: "",
  max_monthly_duty: 12,
  preferred_shift: "flexible" as PreferredShift,
  weekly_off_day: "Friday",
  is_active: true
};

type DoctorForm = typeof emptyForm;

export function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [search, setSearch] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<DoctorForm>(emptyForm);
  const searchRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [doctorRows, departmentRows] = await Promise.all([
        doctorApi.list({
          search: search || undefined,
          department_id: departmentFilter ? Number(departmentFilter) : undefined,
          is_active: true
        }),
        doctorApi.departments()
      ]);
      setDoctors(doctorRows);
      setDepartments(departmentRows);
      if (!form.department_id && departmentRows[0]) {
        setForm((current) => ({ ...current, department_id: departmentRows[0].id }));
      }
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [departmentFilter, form.department_id, search]);

  useEffect(() => {
    load();
  }, [load]);

  useKeyboardShortcuts({
    "Ctrl+K": () => searchRef.current?.focus()
  });

  function resetForm() {
    setEditingId(null);
    setForm({ ...emptyForm, department_id: departments[0]?.id ?? 0 });
  }

  function editDoctor(doctor: Doctor) {
    setEditingId(doctor.id);
    setForm({
      name: doctor.name,
      email: doctor.email,
      phone: doctor.phone,
      department_id: doctor.department_id,
      designation: doctor.designation,
      max_monthly_duty: doctor.max_monthly_duty,
      preferred_shift: doctor.preferred_shift,
      weekly_off_day: doctor.weekly_off_day,
      is_active: doctor.is_active
    });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      if (editingId) {
        await doctorApi.update(editingId, form);
        toast.success("Doctor updated");
      } else {
        await doctorApi.create({ ...form, create_user_account: true, initial_password: "Doctor@123" });
        toast.success("Doctor added");
      }
      resetForm();
      load();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  async function removeDoctor(id: number) {
    try {
      await doctorApi.remove(id);
      toast.success("Doctor deactivated");
      load();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Doctor Management"
        title="Doctors, Departments and Availability"
        actions={
          <Button onClick={resetForm}>
            <Plus className="h-4 w-4" />
            Add doctor
          </Button>
        }
      />

      <section className="grid gap-6 xl:grid-cols-[1fr_390px]">
        <Card className="min-w-0">
          <CardHeader>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <CardTitle>Active Doctors</CardTitle>
              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    ref={searchRef}
                    className="min-w-72 pl-9"
                    placeholder="Search doctors"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </div>
                <Select value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)}>
                  <option value="">All departments</option>
                  {departments.map((department) => (
                    <option key={department.id} value={department.id}>
                      {department.name}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[920px] border-separate border-spacing-0 text-sm">
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th className="border-b p-3 font-medium">Doctor</th>
                    <th className="border-b p-3 font-medium">Department</th>
                    <th className="border-b p-3 font-medium">Designation</th>
                    <th className="border-b p-3 font-medium">Shift</th>
                    <th className="border-b p-3 font-medium">Off day</th>
                    <th className="border-b p-3 font-medium">Max</th>
                    <th className="border-b p-3 font-medium">Status</th>
                    <th className="border-b p-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {doctors.map((doctor) => (
                    <tr key={doctor.id} className="hover:bg-secondary/40">
                      <td className="border-b p-3">
                        <p className="font-semibold">{doctor.name}</p>
                        <p className="text-xs text-muted-foreground">{doctor.email}</p>
                      </td>
                      <td className="border-b p-3">{doctor.department.name}</td>
                      <td className="border-b p-3">{doctor.designation}</td>
                      <td className="border-b p-3 capitalize">{doctor.preferred_shift}</td>
                      <td className="border-b p-3">{doctor.weekly_off_day}</td>
                      <td className="border-b p-3">{doctor.max_monthly_duty}</td>
                      <td className="border-b p-3">
                        <Badge variant={doctor.is_active ? "default" : "secondary"}>
                          {doctor.is_active ? <CheckCircle2 className="mr-1 h-3 w-3" /> : <XCircle className="mr-1 h-3 w-3" />}
                          {doctor.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </td>
                      <td className="border-b p-3">
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" size="icon" aria-label="Edit doctor" onClick={() => editDoctor(doctor)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button variant="destructive" size="icon" aria-label="Deactivate doctor" onClick={() => removeDoctor(doctor.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!doctors.length && (
                    <tr>
                      <td className="p-8 text-center text-muted-foreground" colSpan={8}>
                        {loading ? "Loading doctors..." : "No doctors found"}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{editingId ? "Edit Doctor" : "Add Doctor"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-2">
                <Label>Name</Label>
                <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} required />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Department</Label>
                  <Select value={form.department_id} onChange={(event) => setForm({ ...form, department_id: Number(event.target.value) })}>
                    {departments.map((department) => (
                      <option key={department.id} value={department.id}>
                        {department.name}
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Designation</Label>
                  <Input value={form.designation} onChange={(event) => setForm({ ...form, designation: event.target.value })} required />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label>Max duties</Label>
                  <Input
                    type="number"
                    min={1}
                    max={31}
                    value={form.max_monthly_duty}
                    onChange={(event) => setForm({ ...form, max_monthly_duty: Number(event.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Shift</Label>
                  <Select value={form.preferred_shift} onChange={(event) => setForm({ ...form, preferred_shift: event.target.value as PreferredShift })}>
                    <option value="flexible">Flexible</option>
                    <option value="morning">Morning</option>
                    <option value="evening">Evening</option>
                    <option value="night">Night</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Off day</Label>
                  <Select value={form.weekly_off_day} onChange={(event) => setForm({ ...form, weekly_off_day: event.target.value })}>
                    {["Friday", "Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"].map((day) => (
                      <option key={day} value={day}>
                        {day}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button className="flex-1">{editingId ? "Save changes" : "Create doctor"}</Button>
                {editingId ? (
                  <Button type="button" variant="secondary" onClick={resetForm}>
                    Cancel
                  </Button>
                ) : null}
              </div>
            </form>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
