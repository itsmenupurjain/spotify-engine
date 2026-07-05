"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Home,
  MessageCircleQuestion,
  Layers,
  Users,
  Target,
  Quote,
  Activity,
} from "lucide-react";
import { fetchHealth } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Intelligence Home", icon: Home },
  { href: "/query", label: "Ask a Question", icon: MessageCircleQuestion },
  { href: "/themes", label: "Theme Explorer", icon: Layers },
  { href: "/segments", label: "Segment Breakdown", icon: Users },
  { href: "/opportunities", label: "Opportunity Map", icon: Target },
  { href: "/quotes", label: "Quote Library", icon: Quote },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [healthStatus, setHealthStatus] = useState<"healthy" | "degraded" | "offline">("healthy");
  const [lastChecked, setLastChecked] = useState<string>("Checking...");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await fetchHealth();
        const allHealthy = health.checks
          ? Object.values(health.checks).every((c: any) => c.status === "ok" || c.status === "healthy")
          : health.status === "ok" || health.status === "healthy";

        setHealthStatus(allHealthy ? "healthy" : "degraded");
        setLastChecked("Just now");
      } catch {
        setHealthStatus("offline");
        setLastChecked("API unreachable");
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const statusConfig = {
    healthy: { color: "var(--color-accent-green)", label: "System Healthy" },
    degraded: { color: "#f59e0b", label: "Degraded" },
    offline: { color: "#ef4444", label: "API Offline" },
  };

  const status = statusConfig[healthStatus];

  return (
    <aside className="sidebar fixed top-0 left-0 h-screen w-[260px] flex flex-col z-50">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--color-accent-green)] to-[var(--color-accent-purple)] flex items-center justify-center">
            <Activity size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-[var(--color-text-primary)] leading-tight">
              Discovery Engine
            </h1>
            <p className="text-[11px] text-[var(--color-text-muted)] font-medium">
              Spotify Growth Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-link ${isActive ? "active" : ""}`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Health Status Footer */}
      <div className="px-4 py-4 border-t border-[var(--color-border)]">
        <div className="flex items-center gap-2 px-3 py-2">
          <div
            className={`w-2 h-2 rounded-full ${healthStatus === "healthy" ? "animate-pulse-glow" : ""}`}
            style={{ background: status.color }}
          />
          <span className="text-[12px] text-[var(--color-text-muted)] font-medium">
            {status.label}
          </span>
        </div>
        <p className="text-[11px] text-[var(--color-text-muted)] px-3 mt-1">
          v1.0 — AI Review Intelligence
        </p>
      </div>
    </aside>
  );
}
