import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Search, FileText, Zap, CheckCircle2, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />
        
        <div className="container relative mx-auto px-4 py-20 md:py-32">
          <div className="max-w-3xl mx-auto text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-4">
              <Shield className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Security Testing Made Simple</span>
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
              Hack Your Own Web
            </h1>
            
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              A beginner-friendly web vulnerability scanner that helps you test websites for common security flaws. 
              Educational, powerful, and easy to use.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <Button asChild size="lg" className="text-lg">
                <Link to="/auth/register">Get Started Free</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="text-lg">
                <Link to="/auth/login">Sign In</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Comprehensive Security Testing</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Automated vulnerability scanning with AI-powered insights and remediation guidance
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            <Card>
              <CardHeader>
                <Search className="h-10 w-10 text-primary mb-2" />
                <CardTitle>SQL Injection Detection</CardTitle>
                <CardDescription>
                  Test forms and parameters for SQL injection vulnerabilities
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <AlertTriangle className="h-10 w-10 text-primary mb-2" />
                <CardTitle>XSS Testing</CardTitle>
                <CardDescription>
                  Identify reflected cross-site scripting vulnerabilities
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Shield className="h-10 w-10 text-primary mb-2" />
                <CardTitle>Security Headers</CardTitle>
                <CardDescription>
                  Check for missing or misconfigured security headers
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Zap className="h-10 w-10 text-primary mb-2" />
                <CardTitle>Open Redirect</CardTitle>
                <CardDescription>
                  Detect open redirect vulnerabilities in your application
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <FileText className="h-10 w-10 text-primary mb-2" />
                <CardTitle>Detailed Reports</CardTitle>
                <CardDescription>
                  Get comprehensive reports with severity levels and evidence
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <CheckCircle2 className="h-10 w-10 text-primary mb-2" />
                <CardTitle>AI Recommendations</CardTitle>
                <CardDescription>
                  Receive AI-powered remediation guidance and sample fixes
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Simple three-step process to start securing your web applications
            </p>
          </div>

          <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-8">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h3 className="text-xl font-semibold">Add Your Domain</h3>
              <p className="text-muted-foreground">
                Register your domain and verify ownership via DNS TXT record
              </p>
            </div>

            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <span className="text-2xl font-bold text-primary">2</span>
              </div>
              <h3 className="text-xl font-semibold">Run Scans</h3>
              <p className="text-muted-foreground">
                Select your target URL and choose which vulnerability checks to run
              </p>
            </div>

            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <span className="text-2xl font-bold text-primary">3</span>
              </div>
              <h3 className="text-xl font-semibold">Review Results</h3>
              <p className="text-muted-foreground">
                Get detailed findings with AI-powered recommendations and fixes
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-primary/5">
        <div className="container mx-auto px-4">
          <Card className="max-w-3xl mx-auto text-center border-primary/20">
            <CardHeader className="space-y-4 pb-8">
              <CardTitle className="text-3xl">Ready to Secure Your Web App?</CardTitle>
              <CardDescription className="text-lg">
                Start testing your websites for vulnerabilities today. Free to get started.
              </CardDescription>
              <div className="pt-4">
                <Button asChild size="lg" className="text-lg">
                  <Link to="/auth/register">Create Free Account</Link>
                </Button>
              </div>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <span className="font-semibold">HYOW</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 Hack Your Own Web. Educational purposes only.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
