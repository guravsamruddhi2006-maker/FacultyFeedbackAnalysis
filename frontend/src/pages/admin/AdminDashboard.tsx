import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BookOpen, GraduationCap, MessageSquareText, Users } from "lucide-react";

import {
  Alert,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  LoadingBlock,
  PageHeader,
  Select,
  StatCard,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { useToast } from "@/context/ToastContext";
import { ApiError, downloadReport } from "@/lib/api";

interface AdminAnalytics {
  counts: {
    total_students: number;
    total_faculty: number;
    pending_faculty: number;
    total_subjects: number;
    total_course_offerings: number;
    active_feedback_periods: number;
    offering_count: number;
    feedback_count: number;
    average_rating: number;
  };
  submission_rate: number;
  submission_rate_note: string;
  faculty_performance: Array<{
    faculty_id: number;
    name: string;
    offering_count: number;
    response_count: number;
    average_rating: number;
  }>;
  semester_analytics: Array<{ semester_number: number; response_count: number; average_rating: number }>;
  academic_year_comparison: Array<{ academic_year: string; response_count: number; average_rating: number }>;
  question_stats: Array<{ question_id: number; question_text: string; average_rating: number; response_count: number }>;
  improvement_areas: Array<{ title: string; evidence: string; average_rating: number; response_count: number }>;
  filter_options: {
    academic_years: string[];
    semesters: number[];
    subjects: Array<{ subject_code: string; subject_name: string }>;
  };
  privacy_notice: string;
}

export function AdminDashboard() {
  const [filters, setFilters] = useState({ year: "", semester: "", subject: "" });
  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.year) params.set("academic_year", filters.year);
    if (filters.semester) params.set("semester_number", filters.semester);
    if (filters.subject) params.set("subject_code", filters.subject);
    const value = params.toString();
    return value ? `?${value}` : "";
  }, [filters]);
  const { data, loading, error } = useApi<AdminAnalytics>(`/analytics/admin${query}`);
  const { notify } = useToast();
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);

  const exportReport = async (format: "csv" | "pdf") => {
    const params = new URLSearchParams();
    if (filters.year) params.set("academic_year", filters.year);
    if (filters.semester) params.set("semester_number", filters.semester);
    if (filters.subject) params.set("subject_code", filters.subject);
    const queryStringValue = params.toString();
    setExporting(format);
    try {
      await downloadReport(
        `/reports/admin${queryStringValue ? `?${queryStringValue}` : ""}`,
        format,
        `department-analytics.${format}`,
      );
      notify(`Department report exported as ${format.toUpperCase()}.`, "success");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "The report could not be exported.", "error");
    } finally {
      setExporting(null);
    }
  };

  if (loading && !data) return <LoadingBlock label="Loading department analytics…" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Department overview"
        description="Department-wide feedback coverage and performance, shown only as aggregate data."
        actions={
          <div className="flex gap-2">
            <Button size="sm" variant="outline" loading={exporting === "csv"} onClick={() => void exportReport("csv")}>
              Export CSV
            </Button>
            <Button size="sm" variant="outline" loading={exporting === "pdf"} onClick={() => void exportReport("pdf")}>
              Export PDF
            </Button>
          </div>
        }
      />
      {error ? <Alert variant="error">{error}</Alert> : null}

      {data ? (
        <>
          <Card>
            <CardContent className="grid gap-3 sm:grid-cols-3">
              <Select
                aria-label="Filter by academic year"
                value={filters.year}
                onChange={(event) => setFilters({ ...filters, year: event.target.value })}
              >
                <option value="">All academic years</option>
                {data.filter_options.academic_years.map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </Select>
              <Select
                aria-label="Filter by semester"
                value={filters.semester}
                onChange={(event) => setFilters({ ...filters, semester: event.target.value })}
              >
                <option value="">All semesters</option>
                {data.filter_options.semesters.map((semester) => (
                  <option key={semester} value={semester}>Semester {semester}</option>
                ))}
              </Select>
              <Select
                aria-label="Filter by subject"
                value={filters.subject}
                onChange={(event) => setFilters({ ...filters, subject: event.target.value })}
              >
                <option value="">All subjects</option>
                {data.filter_options.subjects.map((subject) => (
                  <option key={subject.subject_code} value={subject.subject_code}>
                    {subject.subject_code} · {subject.subject_name}
                  </option>
                ))}
              </Select>
            </CardContent>
          </Card>

          {loading ? <LoadingBlock label="Updating analytics…" /> : null}

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Students" value={data.counts.total_students} icon={<Users className="h-5 w-5" />} />
            <StatCard
              label="Faculty"
              value={data.counts.total_faculty}
              hint={`${data.counts.pending_faculty} awaiting review`}
              icon={<GraduationCap className="h-5 w-5" />}
              tone="violet"
            />
            <StatCard
              label="Subjects"
              value={data.counts.total_subjects}
              hint={`${data.counts.total_course_offerings} course offerings`}
              icon={<BookOpen className="h-5 w-5" />}
              tone="emerald"
            />
            <StatCard
              label="Feedback responses"
              value={data.counts.feedback_count}
              hint={`${data.submission_rate}% coverage indicator`}
              icon={<MessageSquareText className="h-5 w-5" />}
              tone="amber"
            />
          </div>

          <Alert variant="info">{data.privacy_notice} {data.submission_rate_note}</Alert>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Performance by academic year</CardTitle></CardHeader>
              <CardContent className="h-80">
                {data.academic_year_comparison.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.academic_year_comparison}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="academic_year" />
                      <YAxis domain={[0, 5]} />
                      <Tooltip />
                      <Bar dataKey="average_rating" name="Average rating" fill="#2563eb" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <EmptyState title="No year-level feedback data" />}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Feedback responses by semester</CardTitle></CardHeader>
              <CardContent className="h-80">
                {data.semester_analytics.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.semester_analytics}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="semester_number" tickFormatter={(value) => `Sem ${value}`} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="response_count" name="Responses" fill="#0f766e" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <EmptyState title="No semester-level feedback data" />}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader><CardTitle>Faculty performance</CardTitle></CardHeader>
            <CardContent>
              {data.faculty_performance.length ? (
                <Table>
                  <thead><tr><Th>Faculty</Th><Th>Offerings</Th><Th>Responses</Th><Th>Average rating</Th></tr></thead>
                  <tbody>
                    {data.faculty_performance.map((faculty) => (
                      <tr key={faculty.faculty_id}>
                        <Td>{faculty.name}</Td>
                        <Td>{faculty.offering_count}</Td>
                        <Td>{faculty.response_count}</Td>
                        <Td>{faculty.response_count ? `${faculty.average_rating.toFixed(2)} / 5` : "—"}</Td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : <EmptyState title="No faculty performance data" description="Performance appears after feedback is submitted." />}
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Question-level averages</CardTitle></CardHeader>
              <CardContent className="h-80">
                {data.question_stats.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.question_stats} layout="vertical" margin={{ left: 16, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 5]} />
                      <YAxis type="category" dataKey="question_text" width={150} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="average_rating" name="Average rating" fill="#7c3aed" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <EmptyState title="No question ratings yet" />}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Department improvement opportunities</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {data.improvement_areas.length ? data.improvement_areas.map((item) => (
                  <div className="rounded-lg bg-amber-50 p-3" key={item.title}>
                    <p className="text-sm font-semibold text-amber-900">{item.title}</p>
                    <p className="mt-1 text-xs text-amber-800">{item.evidence}</p>
                  </div>
                )) : <EmptyState title="No improvement areas identified" />}
              </CardContent>
            </Card>
          </div>
        </>
      ) : error ? null : <EmptyState title="No analytics data" />}
    </div>
  );
}
