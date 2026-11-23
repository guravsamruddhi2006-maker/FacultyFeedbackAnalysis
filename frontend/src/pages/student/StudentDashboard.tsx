import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  ClipboardList,
  Clock,
  Lock,
  MessageSquarePlus,
  PencilLine,
} from "lucide-react";

import { PageHeader, Card, CardContent, Badge, Button, Select, StatCard, LoadingBlock, Alert, EmptyState, Table, Th, Td } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { formatDate, formatDateTime } from "@/lib/utils";
import type { Offering } from "@/lib/types";

interface StudentDashboardResponse {
  student: { student_id: string; name: string };
  filter_options: {
    academic_years: string[];
    semesters: number[];
    periods: Array<{ semester_number: number; start_date: string; end_date: string; is_open: boolean }>;
  };
  selected: { academic_year: string | null; semester_number: number | null };
  offerings: Offering[];
  summary: { submitted: number; pending: number; closed: number; total: number };
}

export function StudentDashboard() {
  const [filters, setFilters] = useState<{ year?: string; semester?: number }>({});
  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.year) params.set("academic_year", filters.year);
    if (filters.semester) params.set("semester_number", String(filters.semester));
    const value = params.toString();
    return value ? `?${value}` : "";
  }, [filters]);

  const { data, loading, error, reload } = useApi<StudentDashboardResponse>(`/students/me/dashboard${query}`);

  const selectedYear = filters.year ?? data?.selected.academic_year ?? "";
  const selectedSemester = filters.semester ?? data?.selected.semester_number ?? "";
  const openPeriod = data?.filter_options.periods.find((period) => period.is_open);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Hello, ${data?.student.name?.split(" ")[0] ?? "student"}`}
        description="Your feedback is anonymous. Faculty only see aggregated ratings and the comment text — never your identity."
      />

      {error ? <Alert variant="error">{error}</Alert> : null}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Submitted"
          value={data?.summary.submitted ?? "—"}
          hint="Courses completed this semester"
          icon={<CheckCircle2 className="h-5 w-5" />}
          tone="emerald"
        />
        <StatCard
          label="Pending"
          value={data?.summary.pending ?? "—"}
          hint="Open for feedback right now"
          icon={<Clock className="h-5 w-5" />}
          tone="amber"
        />
        <StatCard
          label="Closed"
          value={data?.summary.closed ?? "—"}
          hint="Period finished, not submitted"
          icon={<Lock className="h-5 w-5" />}
          tone="slate"
        />
      </div>

      <Card>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="grid flex-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500" htmlFor="year">
                  Academic year
                </label>
                <Select
                  id="year"
                  value={selectedYear}
                  onChange={(event) => setFilters({ ...filters, year: event.target.value })}
                >
                  {(data?.filter_options.academic_years ?? []).map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500" htmlFor="semester">
                  Semester
                </label>
                <Select
                  id="semester"
                  value={selectedSemester}
                  onChange={(event) => setFilters({ ...filters, semester: Number(event.target.value) })}
                >
                  {(data?.filter_options.semesters ?? []).map((semester) => (
                    <option key={semester} value={semester}>
                      Semester {semester}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <Button variant="outline" onClick={reload}>
              Refresh
            </Button>
          </div>

          {openPeriod ? (
            <Alert variant="info" title="Feedback window open">
              Open until {formatDate(openPeriod.end_date)}. You can edit your responses while the window is open.
            </Alert>
          ) : (
            <Alert variant="warning" title="No open feedback window">
              Feedback for the selected semester is closed. Choose another year or semester to review past submissions.
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <div className="border-b px-5 py-4">
          <h2 className="font-semibold text-slate-900">Subjects and faculty</h2>
          <p className="text-sm text-slate-500">
            Only subjects with an active faculty selection for this year and semester are shown.
          </p>
        </div>
        {loading ? (
          <LoadingBlock />
        ) : !data?.offerings.length ? (
          <EmptyState
            title="No subjects available for this semester yet."
            description="Subjects appear here only after an approved faculty member selects them for this academic year and semester."
            icon={<ClipboardList className="h-6 w-6" />}
          />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Course</Th>
                <Th>Faculty</Th>
                <Th>Status</Th>
                <Th className="text-right">Action</Th>
              </tr>
            </thead>
            <tbody>
              {data.offerings.map((offering) => (
                <tr key={offering.offering_id} className="hover:bg-slate-50/70">
                  <Td>
                    <p className="font-medium text-slate-900">{offering.subject_code}</p>
                    <p className="text-xs text-slate-500">{offering.subject_name}</p>
                  </Td>
                  <Td>{offering.faculty_name}</Td>
                  <Td>
                    <div className="space-y-1">
                      <Badge
                        variant={
                          offering.status === "submitted"
                            ? "success"
                            : offering.status === "pending"
                              ? "warning"
                              : "outline"
                        }
                      >
                        {offering.status}
                      </Badge>
                      {offering.submitted_at ? (
                        <p className="text-xs text-slate-400">{formatDateTime(offering.submitted_at)}</p>
                      ) : null}
                    </div>
                  </Td>
                  <Td className="text-right">
                    {offering.status === "pending" || (offering.status === "submitted" && offering.period_open) ? (
                      <Link to={`/student/feedback/${offering.offering_id}`}>
                        <Button size="sm" variant={offering.status === "submitted" ? "outline" : "primary"}>
                          {offering.status === "submitted" ? (
                            <>
                              <PencilLine className="h-3.5 w-3.5" /> Edit
                            </>
                          ) : (
                            <>
                              <MessageSquarePlus className="h-3.5 w-3.5" /> Give feedback
                            </>
                          )}
                        </Button>
                      </Link>
                    ) : offering.status === "submitted" ? (
                      <Link to={`/student/feedback/${offering.offering_id}`}>
                        <Button size="sm" variant="ghost">
                          View
                        </Button>
                      </Link>
                    ) : (
                      <span className="text-xs text-slate-400">Closed</span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
