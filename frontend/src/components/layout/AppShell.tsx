import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { BarChart3, CalendarDays, ClipboardList, LayoutDashboard, LogOut, Stethoscope, UserRoundCog } from "lucide-react";

import { Button } from "@/components/ui/button";
import { isAdminRole } from "@/lib/roles";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/doctors", label: "Doctors", icon: Stethoscope },
  { href: "/leaves", label: "Leaves", icon: CalendarDays },
  { href: "/roster", label: "Roster", icon: ClipboardList },
  { href: "/analytics", label: "Analytics", icon: BarChart3 }
];

export function AppShell() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const visibleNavigation = isAdminRole(user?.role) ? navigation : navigation.filter((item) => item.href === "/roster");

  return (
    <div className="min-h-screen">
      <aside className="no-print fixed inset-y-0 left-0 z-30 hidden w-72 border-r bg-background/88 backdrop-blur xl:block">
        <div className="flex h-full flex-col">
          <div className="border-b p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <UserRoundCog className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Bangladesh Hospital ERP</p>
                <h1 className="text-lg font-bold tracking-normal">Doctor Duty Roster</h1>
              </div>
            </div>
          </div>
          <nav className="flex-1 space-y-1 p-4">
            {visibleNavigation.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-secondary hover:text-foreground",
                    isActive && "bg-secondary text-foreground"
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="border-t p-4">
            <div className="mb-3 rounded-md bg-secondary p-3">
              <p className="truncate text-sm font-semibold">{user?.full_name}</p>
              <p className="truncate text-xs text-muted-foreground">{user?.role.replace("_", " ")}</p>
            </div>
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </aside>

      <div className="xl:pl-72">
        <header className="no-print sticky top-0 z-20 border-b bg-background/88 px-4 py-3 backdrop-blur xl:hidden">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Doctor Duty Roster</p>
              <p className="font-semibold">{user?.full_name}</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Sign out"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
          <nav className="mt-3 flex gap-2 overflow-x-auto pb-1">
            {visibleNavigation.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground",
                    isActive && "bg-secondary text-foreground"
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-[1540px] px-4 py-6 md:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
