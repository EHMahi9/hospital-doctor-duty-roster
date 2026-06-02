import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { LockKeyhole, Mail, Stethoscope, UserRoundPlus } from "lucide-react";
import { toast } from "sonner";

import { errorMessage } from "@/api/client";
import { authApi } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useAuthStore } from "@/store/authStore";
import type { RegisterPayload } from "@/types/api";

export function RegisterPage() {
  const navigate = useNavigate();
  const { token, setSession } = useAuthStore();
  const [form, setForm] = useState<RegisterPayload>({
    full_name: "",
    email: "",
    password: "",
    account_type: "staff"
  });
  const [loading, setLoading] = useState(false);

  if (token) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const response = await authApi.register(form);
      setSession(response.access_token, response.user);
      toast.success("Account created successfully");
      navigate("/");
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl gap-8 lg:grid-cols-[1fr_0.95fr] lg:items-center">
        <section>
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Stethoscope className="h-7 w-7" />
          </div>
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-primary">Roster Access</p>
          <h1 className="max-w-2xl text-4xl font-bold tracking-normal text-foreground md:text-6xl">
            View monthly hospital duty routines securely
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground">
            Staff can create a view-only roster account. Doctors must use the email already registered in doctor management.
          </p>
        </section>

        <Card className="w-full">
          <CardHeader>
            <CardTitle>Create Account</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" autoComplete="off" onSubmit={onSubmit}>
              <div className="space-y-2">
                <Label htmlFor="full-name">Full name</Label>
                <div className="relative">
                  <UserRoundPlus className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="full-name"
                    name="register-full-name"
                    autoComplete="off"
                    className="pl-9"
                    value={form.full_name}
                    onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="register-email">Email</Label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="register-email"
                    name="register-email"
                    type="email"
                    autoComplete="off"
                    className="pl-9"
                    value={form.email}
                    onChange={(event) => setForm({ ...form, email: event.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="account-type">Account type</Label>
                  <Select
                    id="account-type"
                    value={form.account_type}
                    onChange={(event) => setForm({ ...form, account_type: event.target.value as RegisterPayload["account_type"] })}
                  >
                    <option value="staff">Staff</option>
                    <option value="doctor">Doctor</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-password">Password</Label>
                  <div className="relative">
                    <LockKeyhole className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-password"
                      name="register-password"
                      type="password"
                      autoComplete="new-password"
                      className="pl-9"
                      minLength={8}
                      value={form.password}
                      onChange={(event) => setForm({ ...form, password: event.target.value })}
                      required
                    />
                  </div>
                </div>
              </div>

              <Button className="w-full" disabled={loading}>
                {loading ? "Creating..." : "Create account"}
              </Button>
            </form>

            <div className="mt-4 text-center text-sm text-muted-foreground">
              Already have access?{" "}
              <Link className="font-semibold text-primary hover:text-primary/80" to="/login">
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
