import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { LockKeyhole, Mail, Stethoscope } from "lucide-react";
import { toast } from "sonner";

import { authApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/store/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const { token, setSession } = useAuthStore();
  const [email, setEmail] = useState("momenulislam900@gmail.com");
  const [password, setPassword] = useState("12345678");
  const [loading, setLoading] = useState(false);

  if (token) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const response = await authApi.login(email, password);
      setSession(response.access_token, response.user);
      toast.success("Signed in successfully");
      navigate("/");
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <section>
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Stethoscope className="h-7 w-7" />
          </div>
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-primary">Hospital ERP Roster System</p>
          <h1 className="max-w-2xl text-4xl font-bold tracking-normal text-foreground md:text-6xl">
            Doctor duty scheduling for high-volume Bangladesh hospitals
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground">
            Secure roster generation, leave controls, workload balancing, audit trails, and export-ready monthly duty plans.
          </p>
        </section>
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Secure Login</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" autoComplete="off" onSubmit={onSubmit}>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    name="login-email"
                    type="email"
                    autoComplete="off"
                    className="pl-9"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    name="login-password"
                    type="password"
                    autoComplete="new-password"
                    className="pl-9"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </div>
              </div>
              <Button className="w-full" disabled={loading}>
                {loading ? "Signing in..." : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
