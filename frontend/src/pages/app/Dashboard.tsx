import { Link } from "react-router-dom";
import { Activity, Globe, Plus, Shield, TrendingUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const Dashboard = () => {
  const stats = {
    totalDomains: 3,
    verifiedDomains: 2,
    totalScans: 12,
    recentScans: 5,
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Quick snapshot of your security posture</p>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link to="/app/domains?modal=add">
              <Plus className="h-4 w-4 mr-2" />
              Add Domain
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/app/scans/new">
              <Activity className="h-4 w-4 mr-2" />
              New Scan
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Domains</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDomains}</div>
            <CardDescription>{stats.verifiedDomains} verified</CardDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Scans</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalScans}</div>
            <CardDescription>{stats.recentScans} this week</CardDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Coverage</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">67%</div>
            <CardDescription>Domains scanned in the last 7 days</CardDescription>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Keep Your Momentum</CardTitle>
          <CardDescription>Pick a task to continue improving your security visibility</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <Button asChild variant="outline" className="justify-start gap-2">
            <Link to="/app/domains?modal=add">
              <Globe className="h-4 w-4" />
              Register another domain
            </Link>
          </Button>
          <Button asChild variant="outline" className="justify-start gap-2">
            <Link to="/app/scans/new">
              <Activity className="h-4 w-4" />
              Launch a fresh scan
            </Link>
          </Button>
          <Button asChild variant="outline" className="justify-start gap-2">
            <Link to="/app/scans">
              <TrendingUp className="h-4 w-4" />
              Review previous results
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
