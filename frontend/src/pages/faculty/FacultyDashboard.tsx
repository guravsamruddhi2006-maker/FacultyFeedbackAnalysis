import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BookOpen, MessageSquareText, Star, TrendingUp } from "lucide-react";

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
  Select,
  StatCard,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { ApiError, downloadReport } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import type { Analytics, CommentRow } from "@/lib/types";

interface ComparisonResponse {
  comparison: Array<{
    academic_year: string;
    subject_code: string;
    subject_name: string;
    average_rating: number;
    response_count: number;
  }>;
  delta: number | null;
  direction: string;
  note: string;
}

interface FacultyOffering {
  offering_id: number;
  academic_year: string;
  semester_number: number;
  subject_code: string;
  subject_name: string;
  response_count: number;
  period_open: boolean;
}

function queryString(filters: { year: string; semester: string; subject: string }) {
  const params = new URLSearchParams();
  if (filters.year) params.set("academic_year", filters.year);
  if (filters.semester) params.set("semester_number", filters.semester);
  if (filters.subject) params.set("subject_code", filters.subject);
  const value = params.toString();
  return value ? `?${value}` : "";
}

function CommentList({ comments }: { comments: CommentRow[] }) {
  if (!comments.length) {
    return (
      <EmptyState
        title="No comments yet"
        description="Anonymous comments will appear here after students submit feedback."
        icon={<MessageSquareText className="h-6 w-6" />}
      />
    );
  }

  return (
    <div className="divide-y">
      {comments.map((comment) => (
        <article className="space-y-2 py-4 first:pt-0 last:pb-0" key={comment.feedback_id}>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{comment.subject_code}</Badge>
            <span className="text-xs text-slate-500">
              {comment.academic_year} · Semester {comment.semester_number}
            </span>
            <Badge
              variant={
                comment.sentiment.label === "positive"
                  ? "success"
                  : comment.sentiment.label === "negative"
                    ? "warning"
                    : "default"
              }
            >
              {comment.sentiment.label}
            </Badge>
          </div>
          <p className="text-sm leading-relaxed text-slate-700">{comment.comment}</p>
        </article>
      ))}
    </div>
  );
}

export function FacultyDashboard() {
  const [filters, setFilters] = useState({ year: "", semester: "", subject: "" });
  const query = useMemo(() => queryString(filters), [filters]);
  const dashboard = useApi<Analytics>(`/faculty/me/dashboard${query}`);
  const offerings = useApi<FacultyOffering[]>("/faculty/me/offerings");
  const comparison = useApi<ComparisonResponse>(
    `/faculty/me/trends${filters.subject ? `?subject_code=${encodeURIComponent(filters.subject)}` : ""}`,
  );

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
        `/reports/faculty/me${queryStringValue ? `?${queryStringValue}` : ""}`,
        format,
        `faculty-performance-${data?.faculty_id ?? "current"}.${format}`,
      );
      notify(`Faculty report exported as ${format.toUpperCase()}.`, "success");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "The report could not be exported.", "error");
    } finally {
      setExporting(null);
    }
  };

  const data = dashboard.data;
  const filteredOfferings = (offerings.data ?? []).filter(
    (offering) =>
      (!filters.year || offering.academic_year === filters.year) &&
      (!filters.semester || offering.semester_number === Number(filters.semester)) &&
      (!filters.subject || offering.subject_code === filters.subject),
  );

  if (dashboard.loading && !data) return <LoadingBlock label="Loading your teaching dashboard…" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Teaching overview"
        description="Your selected subjects and feedback insights. Student identities are never shown."
        actions={
          <div className="flex gap-2">
            <Link to="/faculty/subjects">
              <Button size="sm" variant="outline" icon={<BookOpen className="h-4 w-4" />}>
                Manage subjects
              </Button>
            </Link>
            <Button size="sm" variant="outline" loading={exporting === "csv"} onClick={() => void exportReport("csv")}>
              Export CSV
            </Button>
            <Button size="sm" variant="outline" loading={exporting === "pdf"} onClick={() => void exportReport("pdf")}>
              Export PDF
            </Button>
          </div>
        }
      />
      {dashboard.error ? <Alert variant="error">{dashboard.error}</Alert> : null}
      {offerings.error ? <Alert variant="error">{offerings.error}</Alert> : null}
      {comparison.error ? <Alert variant="error">{comparison.error}</Alert> : null}

      <Card>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <Select
            aria-label="Filter by academic year"
            value={filters.year}
            onChange={(event) => setFilters({ ...filters, year: event.target.value })}
          >
            <option value="">All academic years</option>
            {(data?.filter_options.academic_years ?? []).map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Filter by semester"
            value={filters.semester}
            onChange={(event) => setFilters({ ...filters, semester: event.target.value })}
          >
            <option value="">All semesters</option>
            {(data?.filter_options.semesters ?? []).map((semester) => (
              <option key={semester} value={semester}>
                Semester {semester}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Filter by subject"
            value={filters.subject}
            onChange={(event) => setFilters({ ...filters, subject: event.target.value })}
          >
            <option value="">All subjects</option>
            {(data?.filter_options.subjects ?? []).map((subject) => (
              <option key={subject.subject_code} value={subject.subject_code}>
                {subject.subject_code} · {subject.subject_name}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      {dashboard.loading ? <LoadingBlock label="Updating feedback insights…" /> : null}
      {data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Feedback responses"
              value={data.overall.response_count}
              icon={<MessageSquareText className="h-5 w-5" />}
              tone="blue"
            />
            <StatCard
              label="Average rating"
              value={data.overall.response_count ? `${data.overall.average_rating.toFixed(2)} / 5` : "—"}
              icon={<Star className="h-5 w-5" />}
              tone="amber"
            />
            <StatCard
              label="Selected subjects"
              value={filteredOfferings.length}
              icon={<BookOpen className="h-5 w-5" />}
              tone="violet"
            />
            <StatCard
              label="Year-over-year"
              value={comparison.data?.delta == null ? "—" : `${comparison.data.delta > 0 ? "+" : ""}${comparison.data.delta.toFixed(2)}`}
              hint={comparison.data?.direction.replace(/_/g, " ")}
              icon={<TrendingUp className="h-5 w-5" />}
              tone="emerald"
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>My subjects and semesters</CardTitle>
            </CardHeader>
            <CardContent>
              {offerings.loading ? (
                <LoadingBlock label="Loading your subjects…" />
              ) : filteredOfferings.length ? (
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {filteredOfferings.map((offering) => (
                    <div className="rounded-lg border p-4" key={offering.offering_id}>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-semibold text-slate-900">{offering.subject_code}</p>
                          <p className="mt-1 text-sm text-slate-600">{offering.subject_name}</p>
                        </div>
                        <Badge variant={offering.period_open ? "success" : "outline"}>
                          {offering.period_open ? "Feedback open" : "Feedback closed"}
                        </Badge>
                      </div>
                      <p className="mt-3 text-xs text-slate-500">
                        {offering.academic_year} · Semester {offering.semester_number}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {offering.response_count ?? 0} responses
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No subjects selected"
                  description="Choose the subjects you teach from the My subjects page."
                />
              )}
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Question-wise performance</CardTitle>
              </CardHeader>
              <CardContent className="h-80">
                {data.question_stats?.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.question_stats} layout="vertical" margin={{ left: 16, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 5]} />
                      <YAxis
                        type="category"
                        dataKey="question_text"
                        width={150}
                        tick={{ fontSize: 11 }}
                      />
                      <Tooltip />
                      <Bar dataKey="average_rating" name="Average rating" fill="#2563eb" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState title="No ratings to chart" />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Academic-year comparison</CardTitle>
              </CardHeader>
              <CardContent className="h-80">
                {comparison.loading ? (
                  <LoadingBlock label="Loading comparison…" />
                ) : comparison.data?.comparison?.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={comparison.data.comparison}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="academic_year" />
                      <YAxis domain={[0, 5]} />
                      <Tooltip />
                      <Bar dataKey="average_rating" name="Average rating" fill="#0f766e" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState title="Not enough history to compare" description={comparison.data?.note} />
                )}
              </CardContent>
              {comparison.data ? (
                <p className="px-5 pb-4 text-xs text-slate-500">{comparison.data.note}</p>
              ) : null}
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Evidence-based insights</CardTitle>
              <p className="text-sm text-slate-500">
                Derived from real ratings and anonymised comments. Sentiment uses the{" "}
                {data.sentiment.summary.method} method.
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Strengths</h3>
                {data.insights?.strengths?.length ? (
                  <ul className="mt-2 space-y-2">
                    {data.insights.strengths.map((item) => (
                      <li key={item.area} className="rounded-lg bg-emerald-50 p-3">
                        <p className="text-sm font-semibold text-emerald-900">{item.area}</p>
                        <p className="mt-1 text-xs text-emerald-800">{item.average_rating.toFixed(2)} / 5 · {item.response_count} responses</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">No strength reached the evidence threshold yet.</p>
                )}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Improvement areas and recommendations</h3>
                {data.insights?.improvement_areas?.length ? (
                  <ul className="mt-2 space-y-2">
                    {data.insights.improvement_areas.map((item) => (
                      <li key={item.area} className="rounded-lg bg-amber-50 p-3">
                        <p className="text-sm font-semibold text-amber-900">{item.area}</p>
                        <p className="mt-1 text-xs text-amber-800">{item.average_rating.toFixed(2)} / 5 · {item.response_count} responses</p>
                        <p className="mt-1 text-xs text-amber-800">{item.recommendation}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">No improvement area reached the evidence threshold yet.</p>
                )}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Trend insights</h3>
                {data.insights?.trend_insights?.length ? (
                  <ul className="mt-2 space-y-2">
                    {data.insights.trend_insights.map((item, index) => (
                      <li key={index} className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                        {String(item.academic_year ?? "period")} vs {String(item.previous_academic_year ?? "previous")}:{" "}
                        {Number(item.change ?? 0) > 0 ? "+" : ""}
                        {Number(item.change ?? 0).toFixed(2)} · {String(item.direction ?? "")}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">Not enough comparable history to generate a trend insight yet.</p>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Strengths</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.strengths?.length ? data.strengths.map((item) => (
                  <div className="rounded-lg bg-emerald-50 p-3" key={item.title}>
                    <p className="text-sm font-semibold text-emerald-900">{item.title}</p>
                    <p className="mt-1 text-xs text-emerald-800">{item.evidence}</p>
                  </div>
                )) : <EmptyState title="No evidence-based strengths yet" />}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Areas for improvement</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.improvement_areas?.length ? data.improvement_areas.map((item) => (
                  <div className="rounded-lg bg-amber-50 p-3" key={item.title}>
                    <p className="text-sm font-semibold text-amber-900">{item.title}</p>
                    <p className="mt-1 text-xs text-amber-800">{item.evidence}</p>
                  </div>
                )) : <EmptyState title="No improvement areas identified" />}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Sentiment and recurring topics</CardTitle>
              <p className="text-sm text-slate-500">
                Method: {data.sentiment.summary.method}. {data.sentiment.summary.limitations}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg bg-emerald-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">Positive</p>
                  <p className="mt-1 text-xl font-semibold text-emerald-900">
                    {data.sentiment.summary.positive}{" "}
                    <span className="text-sm font-normal">({data.sentiment.summary.positive_pct}%)</span>
                  </p>
                </div>
                <div className="rounded-lg bg-slate-100 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-600">Neutral</p>
                  <p className="mt-1 text-xl font-semibold text-slate-800">
                    {data.sentiment.summary.neutral}{" "}
                    <span className="text-sm font-normal">({data.sentiment.summary.neutral_pct}%)</span>
                  </p>
                </div>
                <div className="rounded-lg bg-amber-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-amber-700">Negative</p>
                  <p className="mt-1 text-xl font-semibold text-amber-900">
                    {data.sentiment.summary.negative}{" "}
                    <span className="text-sm font-normal">({data.sentiment.summary.negative_pct}%)</span>
                  </p>
                </div>
              </div>
              {data.sentiment.topics.length ? (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-800">Recurring topics</p>
                  {data.sentiment.topics.map((topic) => (
                    <div
                      key={topic.topic}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm"
                    >
                      <span className="font-medium text-slate-800">{topic.topic}</span>
                      <span className="text-xs text-slate-500">
                        {topic.mentions} mentions · {topic.positive} positive · {topic.neutral} neutral ·{" "}
                        {topic.negative} negative
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No recurring topics yet"
                  description="Topics appear after students submit written comments."
                />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Anonymous student comments</CardTitle>
            </CardHeader>
            <CardContent>
              {data.privacy_notice ? (
                <Alert variant="info">{data.privacy_notice}</Alert>
              ) : null}
              <div className="mt-4">
                <CommentList comments={data.comments} />
              </div>
            </CardContent>
          </Card>
        </>
      ) : dashboard.error ? null : (
        <EmptyState title="No dashboard data" description="Try adjusting the filters or refresh the page." />
      )}
    </div>
  );
}

interface CommentsResponse {
  items: CommentRow[];
  total: number;
  page: number;
  page_size: number;
  privacy_notice: string;
}

export function FacultyCommentsPage() {
  const [filters, setFilters] = useState({ year: "", semester: "", subject: "", sentiment: "", page: 1 });
  const options = useApi<Analytics["filter_options"]>("/faculty/me/filter-options");
  const query = useMemo(() => {
    const params = new URLSearchParams({ page: String(filters.page), page_size: "20" });
    if (filters.year) params.set("academic_year", filters.year);
    if (filters.semester) params.set("semester_number", filters.semester);
    if (filters.subject) params.set("subject_code", filters.subject);
    if (filters.sentiment) params.set("sentiment", filters.sentiment);
    return `?${params.toString()}`;
  }, [filters]);
  const comments = useApi<CommentsResponse>(`/faculty/me/comments${query}`);
  const pageCount = Math.max(1, Math.ceil((comments.data?.total ?? 0) / (comments.data?.page_size ?? 20)));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student comments"
        description="Comments are anonymous and scoped to your own selected subjects."
      />
      {options.error ? <Alert variant="error">{options.error}</Alert> : null}
      {comments.error ? <Alert variant="error">{comments.error}</Alert> : null}
      <Card>
        <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Select aria-label="Filter comments by academic year" value={filters.year} onChange={(event) => setFilters({ ...filters, year: event.target.value, page: 1 })}>
            <option value="">All academic years</option>
            {(options.data?.academic_years ?? []).map((year) => <option key={year} value={year}>{year}</option>)}
          </Select>
          <Select aria-label="Filter comments by semester" value={filters.semester} onChange={(event) => setFilters({ ...filters, semester: event.target.value, page: 1 })}>
            <option value="">All semesters</option>
            {(options.data?.semesters ?? []).map((semester) => <option key={semester} value={semester}>Semester {semester}</option>)}
          </Select>
          <Select aria-label="Filter comments by subject" value={filters.subject} onChange={(event) => setFilters({ ...filters, subject: event.target.value, page: 1 })}>
            <option value="">All subjects</option>
            {(options.data?.subjects ?? []).map((subject) => <option key={subject.subject_code} value={subject.subject_code}>{subject.subject_code}</option>)}
          </Select>
          <Select aria-label="Filter comments by sentiment" value={filters.sentiment} onChange={(event) => setFilters({ ...filters, sentiment: event.target.value, page: 1 })}>
            <option value="">All sentiment</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </Select>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Anonymous feedback ({comments.data?.total ?? 0})</CardTitle></CardHeader>
        <CardContent>
          {comments.data?.privacy_notice ? <Alert variant="info">{comments.data.privacy_notice}</Alert> : null}
          <div className="mt-4">
            {comments.loading ? <LoadingBlock label="Loading anonymous comments…" /> : comments.data?.items.length ? (
              <>
                <Table>
                  <thead><tr><Th>Comment</Th><Th>Subject</Th><Th>Academic year</Th><Th>Sentiment</Th></tr></thead>
                  <tbody>{comments.data.items.map((item) => (
                    <tr key={item.feedback_id}>
                      <Td className="min-w-[320px] whitespace-normal">{item.comment}</Td>
                      <Td>{item.subject_code} · {item.subject_name}</Td>
                      <Td>{item.academic_year} · Sem {item.semester_number}</Td>
                      <Td><Badge variant={item.sentiment.label === "positive" ? "success" : item.sentiment.label === "negative" ? "warning" : "default"}>{item.sentiment.label}</Badge></Td>
                    </tr>
                  ))}</tbody>
                </Table>
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-xs text-slate-500">Page {filters.page} of {pageCount}</p>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>Previous</Button>
                    <Button size="sm" variant="outline" disabled={filters.page >= pageCount} onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>Next</Button>
                  </div>
                </div>
              </>
            ) : <EmptyState title="No anonymous comments" description="No comments match the selected filters." />}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
