import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  icon: Icon,
  tone = "teal"
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "teal" | "amber" | "rose" | "blue";
}) {
  const tones = {
    teal: "bg-primary/15 text-primary",
    amber: "bg-accent/15 text-accent",
    rose: "bg-destructive/15 text-red-200",
    blue: "bg-sky-500/15 text-sky-200"
  };
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-normal">{value}</p>
        </div>
        <div className={cn("flex h-11 w-11 items-center justify-center rounded-md", tones[tone])}>
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}
