import { Link } from "react-router-dom";
import { ArrowLeft, BookOpen, CalendarClock, ShieldCheck } from "lucide-react";

import {
  Alert,
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  LoadingBlock,
  PageHeader,
} from "@/components/ui";
import { useApi } from "@/hooks/useApi";

interface FacultyProfileResponse {
  faculty_id: number;
  name: string;
  email: string;
  department_id: number;
  department_name: string | null;
  status: string;
  summary: { offering_count: number; subject_count: number };
  offerings: Array<{
    offering_id: number;
    academic_year: string;
    semester_number: number;
    subject_code: string;
    subject_name: string;
  }>;
  privacy_notice: string;
}

export function FacultyProfilePage() {
  const profile = useApi<FacultyProfileResponse>("/faculty/me/profile");

  if (profile.loading) return <LoadingBlock label="Loading your faculty profile…" />;

  if (profile.error || !profile.data) {
    return (
      <div className="space-y-4">
        <Alert variant="error">{profile.error ?? "Your faculty profile could not be loaded."}</Alert>
        <Link to="/faculty">
          <Button variant="outline" icon={<ArrowLeft className="h-4 w-4" />}>
            Back to teaching overview
          </Button>
        </Link>
      </div>
    );
  }

  const data = profile.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.name}
        description="Your faculty profile, subject selections and privacy boundary."
        actions={
          <Link to="/faculty">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4" /> Teaching overview
            </Button>
          </Link>
        }
      />

      <Alert variant="info">
        <span className="flex items-start gap-2">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{data.privacy_notice}</span>
        </span>
      </Alert>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Selected subjects</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{data.summary.offering_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Subject offerings</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{data.summary.subject_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Account status</p>
            <p className="mt-2">
              <Badge variant={data.status === "approved" ? "success" : "warning"}>{data.status}</Badge>
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>My subjects and semesters</CardTitle>
        </CardHeader>
        <CardContent>
          {data.offerings.length ? (
            <div className="divide-y">
              {data.offerings.map((offering) => (
                <div key={offering.offering_id} className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium text-slate-900">
                      {offering.subject_code} — {offering.subject_name}
                    </p>
                    <p className="text-xs text-slate-500">Semester {offering.semester_number}</p>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <CalendarClock className="h-4 w-4 text-slate-400" />
                    {offering.academic_year}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No subjects selected" description="Choose the subjects you teach from the My subjects page." />
          )}
          {data.offerings.length ? (
            <p className="mt-4 flex items-center gap-2 text-xs text-slate-500">
              <BookOpen className="h-4 w-4" /> Selections are scoped to your faculty account only.
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
