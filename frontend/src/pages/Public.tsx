import { Link } from "react-router-dom";
import { ArrowRight, BarChart3, BrainCircuit, ClipboardList, GraduationCap, Lock, ShieldCheck, Sparkles } from "lucide-react";

import { Card, CardContent } from "@/components/ui";

const linkButtonClass =
  "inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

const outlineLinkButtonClass =
  "inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-700 bg-transparent px-4 py-2 text-sm font-medium text-slate-100 transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-700 text-white">
              <GraduationCap className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold leading-tight text-slate-900">FacultyInsight AI</p>
              <p className="text-[11px] text-slate-500">Better teaching, together</p>
            </div>
          </Link>
          <div className="flex items-center gap-2">
            <Link to="/login" className="inline-flex h-9 items-center justify-center rounded-md px-3 text-sm font-medium text-slate-700 hover:bg-slate-100">
              Sign in
            </Link>
            <Link to="/register/student" className="inline-flex h-9 items-center justify-center rounded-md bg-blue-700 px-3 text-sm font-medium text-white shadow-sm hover:bg-blue-800">
              Student access
            </Link>
          </div>
        </div>
      </header>

      <section className="bg-slate-900 text-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium text-slate-200">
              <Sparkles className="h-3.5 w-3.5" /> AI-powered faculty feedback analytics
            </span>
            <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
              Turning student feedback into better teaching.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-slate-300">
              FacultyInsight AI collects structured, anonymous faculty feedback, analyses real rating data with
              transparent statistics and explainable NLP, and turns it into actionable improvement insights.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/login" className={`${linkButtonClass} bg-white text-slate-900 hover:bg-slate-100`}>
                Access the platform <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/about" className={`${outlineLinkButtonClass} hidden sm:inline-flex`}>
                Learn more
              </Link>
            </div>
          </div>
          <Card className="border-slate-800 bg-slate-900/60 text-slate-100">
            <CardContent className="space-y-4 p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                  <p className="text-2xl font-semibold">5</p>
                  <p className="text-xs text-slate-400">Validated feedback questions</p>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                  <p className="text-2xl font-semibold">3</p>
                  <p className="text-xs text-slate-400">Anonymous insight layers</p>
                </div>
              </div>
              <p className="text-sm text-slate-300">
                Every insight is traceable to real aggregated ratings and anonymised comment evidence. No synthetic
                numbers, no personal student data exposed to faculty.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <h2 className="text-center text-2xl font-semibold text-slate-900 sm:text-3xl">Everything feedback teams need</h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-sm text-slate-600">
          One platform for the full feedback lifecycle — from controlled submission to evidence-based teaching analysis.
        </p>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { icon: ClipboardList, title: "Controlled feedback lifecycle", text: "Open, editable and closed feedback periods with one submission per student per course offering." },
            { icon: BarChart3, title: "Real analytics", text: "Department, subject, faculty and semester-level aggregates computed from live database answers." },
            { icon: BrainCircuit, title: "Explainable AI insights", text: "Sentiment analysis, recurring topics, strengths and improvement areas backed by actual responses." },
            { icon: ShieldCheck, title: "Privacy by design", text: "Faculty analytics and reports use aggregated feedback only; student identities are never exposed." },
            { icon: Lock, title: "Secure accounts", text: "JWT sessions, bcrypt password hashing, rate-limited logins and audited administrative actions." },
            { icon: GraduationCap, title: "Three role portals", text: "Student feedback, faculty teaching review and administrative oversight in one application." },
          ].map((item) => (
            <Card key={item.title}>
              <CardContent className="space-y-2 p-5">
                <item.icon className="h-5 w-5 text-blue-700" />
                <h3 className="font-semibold text-slate-900">{item.title}</h3>
                <p className="text-sm text-slate-600">{item.text}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="bg-white">
        <div className="mx-auto max-w-4xl px-4 py-14 text-center sm:px-6">
          <h2 className="text-2xl font-semibold text-slate-900 sm:text-3xl">See how it works</h2>
          <ol className="mt-8 space-y-6 text-left">
            {[
              "An administrator opens a feedback period for an academic year and semester.",
              "Students review their assigned course offerings and submit anonymous ratings and comments.",
              "The analytics engine aggregates real answers into averages, distributions and trends.",
              "The AI layer produces strengths, improvement areas and recommendations from that evidence.",
            ].map((step, index) => (
              <li key={step} className="flex gap-4">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-700 text-sm font-semibold text-white">
                  {index + 1}
                </span>
                <p className="pt-1 text-sm text-slate-700">{step}</p>
              </li>
            ))}
          </ol>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            <Link to="/register/faculty" className={linkButtonClass}>
              Faculty registration
            </Link>
            <Link to="/register/student" className={`${linkButtonClass} bg-emerald-700 hover:bg-emerald-800`}>
              Student registration
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

export function AboutPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-700 text-white">
              <GraduationCap className="h-5 w-5" />
            </div>
            <p className="text-sm font-semibold text-slate-900">FacultyInsight AI</p>
          </Link>
          <Link to="/" className="inline-flex h-9 items-center justify-center rounded-md px-3 text-sm font-medium text-slate-700 hover:bg-slate-100">
            Back to home
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <h1 className="text-3xl font-semibold text-slate-900">About FacultyInsight AI</h1>
        <p className="mt-4 text-slate-700">
          FacultyInsight AI is a feedback management and teaching performance analysis platform. It is built for a
          department that wants honest, structured, anonymous student feedback and fast evidence-based teaching
          improvement.
        </p>
        <div className="mt-8 space-y-6">
          <Card>
            <CardContent className="p-5">
              <h2 className="font-semibold text-slate-900">Mission</h2>
              <p className="mt-2 text-sm text-slate-600">Make teaching improvement continuous, data-informed and privacy-respecting.</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <h2 className="font-semibold text-slate-900">What it measures</h2>
              <p className="mt-2 text-sm text-slate-600">
                Concept clarity, subject knowledge, participation, practical examples and syllabus completion — each on
                a 1–5 validated scale.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <h2 className="font-semibold text-slate-900">Privacy</h2>
              <p className="mt-2 text-sm text-slate-600">
                Faculty and administrator analytics expose aggregates and anonymised comments only. Student identities are
                never part of any analytics or export.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
