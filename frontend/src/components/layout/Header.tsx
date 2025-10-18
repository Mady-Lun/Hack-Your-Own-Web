import { Shield, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useMemo, useState } from "react";
import { useTheme } from "next-themes";
import { useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMe } from "@/api/me";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export const Header = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [isMounted, setIsMounted] = useState(false);
  const location = useLocation();
  const isAppRoute = location.pathname.startsWith("/app");

  const profileQuery = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    enabled: isAppRoute,
  });

  const profile = profileQuery.data ?? null;

  const displayName = useMemo(() => {
    if (!profile) {
      return isAppRoute && profileQuery.isFetching ? "Loading..." : "Guest";
    }

    return (
      profile.display_name?.trim() ||
      [profile.first_name, profile.last_name].filter(Boolean).join(" ").trim() ||
      profile.email ||
      "User"
    );
  }, [profile, profileQuery.isFetching, isAppRoute]);

  const initials = useMemo(() => {
    if (profile?.first_name || profile?.last_name) {
      return `${profile.first_name?.[0] ?? ""}${profile.last_name?.[0] ?? ""}`.toUpperCase() || "U";
    }

    const fallbackSource = displayName || profile?.email || "User";
    const letters = fallbackSource
      .split(" ")
      .filter(Boolean)
      .map((piece) => piece[0])
      .join("")
      .slice(0, 2);
    return letters.toUpperCase() || "U";
  }, [profile, displayName]);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const currentTheme = theme === "system" ? resolvedTheme : theme;
  const isDark = (currentTheme ?? "dark") === "dark";

  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          <span className="font-bold text-xl">HYOW</span>
          <span className="text-xs text-muted-foreground hidden sm:inline">
            Hack Your Own Web
          </span>
        </div>

        <div className="flex items-center gap-3">
          {isAppRoute ? (
            <div className="flex items-center gap-2 rounded-full border bg-card/70 px-3 py-1">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs font-medium">{initials}</AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-foreground">{displayName}</span>
            </div>
          ) : null}

          <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
            {!isMounted ? (
              <Sun className="h-5 w-5" />
            ) : isDark ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </header>
  );
};
