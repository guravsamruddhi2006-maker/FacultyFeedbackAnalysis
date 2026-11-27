import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Copy,
  Download,
  MessageCircle,
  RefreshCw,
  Users,
} from "lucide-react";

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
import { useToast } from "@/context/ToastContext";
import { useApi } from "@/hooks/useApi";
import { ApiError, downloadReport } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { buildReminderMessage, copyToClipboard, whatsappShareUrl } from "@/lib/whatsapp";
import type { CompletionSummary, FacultySelection } from "@/lib/types";

interface Filters {
  academic_year: string;
  semester_number: string;
  subject_code: string;
}

export function FacultyCompletionPage() {
  const { notify } = useToast();
  const selections = useApi<FacultySelection[]>("/faculty/me/selections");
  const [filters, setFilters] = useState<Filters>({
    academic_year: "",
    semester_number: "",
    subject_code: "",
  });
  const [exporting, setExporting] = useState(false);

  const list = useMemo(
    () => (selections.data ?? []).filter((item) => item.is_active),
    [selections.data],
  );

  useEffect(() => {
    if (!list.length) return;
    const stillValid = list.some(
      (item) =>
        item.subject_code === filters.subject_code &&
        item.academic_year === filters.academic_year &&
        String(item.semester_number) === filters.semester_number,
    );
    if (stillValid) return;
    const first = list[0];
    setFilters({
      academic_year: first.academic_year,
      semester_number: String(first.semester_number),
      subject_code: first.subject_code,
    });
  }, [list, filters.subject_code, filters.academic_year, filters.semester_number]);

  const years = useMemo(
    () => Array.from(new Set(list.map((item) => item.academic_year))).sort().reverse(),
    [list],
  );
  const semesters = useMemo(
    () =>
      Array.from(
        new Set(
          list
            .filter((item) => item.academic_year === filters.academic_year)
            .map((item) => item.semester_number),
        ),
      ).sort((a, b) => a - b),
    [list, filters.academic_year],
  );
  const subjects = useMemo(
    () =>
      list.filter(
        (item) =>
          item.academic_year === filters.academic_year &&
          String(item.semester_number) === filters.semester_number,
      ),
    [list, filters.academic_year, filters.semester_number],
  );

  const query = useMemo(() => {
    if (!filters.subject_code || !filters.academic_year || !filters.semester_number) return null;
    const params = new URLSearchParams({
      subject_code: filters.subject_code,
      academic_year: filters.academic_year,
      semester_number: filters.semester_number,
    });
    return `/faculty/me/completion?${params.toString()}`;
  }, [filters]);

  const completion = useApi<CompletionSummary>(query);
  const data = completion.data;

  const changeYear = (academic_year: string) => {
    const sameSemester = list.find(
      (item) =>
        item.academic_year === academic_year &&
        String(item.semester_number) === filters.semester_number,
    );
    const match = sameSemester ?? list.find((item) => item.academic_year === academic_year);
    setFilters({
      academic_year,
      semester_number: match ? String(match.semester_number) : "",
      subject_code: match?.subject_code ?? "",
    });
  };

  const changeSemester = (semester_number: string) => {
    const match = list.find(
      (item) =>
        item.academic_year === filters.academic_year &&
        String(item.semester_number) === semester_number,
    );
    setFilters({ ...filters, semester_number, subject_code: match?.subject_code ?? "" });
  };

  const reminder = data
    ? buildReminderMessage({
        subjectCode: data.subject_code,
        subjectName: data.subject_name,
        academicYear: data.academic_year,
        semesterNumber: data.semester_number,
        eligibleCount: data.eligible_count,
        submittedCount: data.submitted_count,
        pendingCount: data.pending_count,
        completionPercentage: data.completion_percentage,
      })
    : "";

  const downloadPdf = async () => {
    if (!data?.roster_available || !query) return;
    setExporting(true);
    try {
      await downloadReport(
        `/reports/faculty/me/completion?${query.split("?")[1]}`,
        "pdf",
        `feedback-completion-${data.subject_code}.pdf`,
      );
      notify("Completion report downloaded.", "success");
    } catch (error) {
      notify(
        error instanceof ApiError ? error.message : "The completion report could not be downloaded.",
        "error",
      );
    } finally {
      setExporting(false);
    }
  };

  const shareWhatsApp = () => {
    if (!reminder) return;
    window.open(whatsappShareUrl(reminder), "_blank", "noopener,noreferrer");
  };

  const copyReminder = async () => {
    if (!reminder) return;
    const copied = await copyToClipboard(reminder);
    notify(
      copied ? "Reminder copied. Paste it into your class group." : "The reminder could not be copied.",
      copied ? "success" : "error",
    );
  };

  if (selections.loading && !selections.data) {
    return <LoadingBlock label="Loading your selected subjects…" />;
  }

  if (selections.error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Completion tracker" description="Feedback completion for your own subjects." />
        <Alert variant="error">{selections.error}</Alert>
      </div>
    );
  }

  if (!list.length) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Completion tracker"
          description="See who has submitted without seeing what anyone said."
        />
        <EmptyState
          title="Select a subject first"
          description="Completion tracking uses the subjects you teach. Add an active subject selection, then return here."
          icon={<ClipboardCheck className="h-6 w-6" />}
          action={
            <Link to="/faculty/subjects">
              <Button size="sm">Manage my subjects</Button>
            </Link>
          }
        />
      </div>
    );
  }

  const percentage = Math.min(100, Math.max(0, data?.completion_percentage ?? 0));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Completion tracker"
        description="See who has submitted without seeing what anyone said. Counts use the verified class roster only."
        actions={
          <Button
            variant="outline"
            size="sm"
            icon={<RefreshCw className="h-3.5 w-3.5" />}
            loading={completion.loading}
            onClick={() => completion.reload()}
          >
            Refresh
          </Button>
        }
      />

      {completion.error ? <Alert variant="error">{completion.error}</Alert> : null}

      <Card>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <Select
            aria-label="Academic year"
            value={filters.academic_year}
            onChange={(event) => changeYear(event.target.value)}
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Semester"
            value={filters.semester_number}
            onChange={(event) => changeSemester(event.target.value)}
          >
            {semesters.map((semester) => (
              <option key={semester} value={semester}>
                Semester {semester}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Subject"
            value={filters.subject_code}
            onChange={(event) => setFilters({ ...filters, subject_code: event.target.value })}
          >
            {subjects.map((subject) => (
              <option key={subject.subject_code} value={subject.subject_code}>
                {subject.subject_code} — {subject.subject_name}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      {completion.loading && !data ? <LoadingBlock label="Calculating completion…" /> : null}

      {data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Eligible students"
              value={data.eligible_count}
              hint="On the verified roster"
              icon={<Users className="h-5 w-5" />}
              tone="blue"
            />
            <StatCard
              label="Submitted"
              value={data.submitted_count}
              hint="Feedback received"
              icon={<CheckCircle2 className="h-5 w-5" />}
              tone="emerald"
            />
            <StatCard
              label="Pending"
              value={data.pending_count}
              hint="Not submitted yet"
              icon={<AlertTriangle className="h-5 w-5" />}
              tone="amber"
            />
            <StatCard
              label="Completion"
              value={`${data.completion_percentage.toFixed(1)}%`}
              hint="Of eligible students"
              icon={<ClipboardCheck className="h-5 w-5" />}
              tone="violet"
            />
          </div>

          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <CardTitle>
                    {data.subject_code} — {data.subject_name}
                  </CardTitle>
                  <p className="mt-1 text-sm text-slate-500">
                    {data.academic_year} · Semester {data.semester_number}
                  </p>
                </div>
                <Badge
                  variant={
                    !data.period ? "warning" : data.period.is_open ? "success" : "outline"
                  }
                >
                  {!data.period
                    ? "No feedback period"
                    : data.period.is_open
                      ? "Feedback window open"
                      : "Feedback window closed"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-slate-700">Submission progress</span>
                  <span className="text-slate-500">
                    {data.submitted_count} / {data.eligible_count} ({data.completion_percentage.toFixed(1)}%)
                  </span>
                </div>
                <div
                  className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-100"
                  role="progressbar"
                  aria-label="Feedback completion"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(percentage)}
                >
                  <div
                    className="h-full rounded-full bg-teal-600 transition-[width] duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>

              {data.period ? (
                <p className="text-xs text-slate-500">
                  Feedback window: {formatDate(data.period.start_date)} to {formatDate(data.period.end_date)}.
                </p>
              ) : (
                <Alert variant="warning" title="Feedback period not configured">
                  Completion can be tracked, but students cannot submit until an administrator
                  configures the feedback window for this academic year and semester.
                </Alert>
              )}

              {!data.roster_available ? (
                <Alert variant="warning" title="Verified class roster not available">
                  <p>
                    Completion cannot be calculated because no active students are on the verified
                    roster for this subject, year and semester. Registered students are never assumed
                    to be enrolled.
                  </p>
                  <p className="mt-2">
                    Ask an administrator to add the class roster under <strong>Class rosters</strong>.
                    Pending lists and PDF exports stay disabled until a verified roster exists.
                  </p>
                </Alert>
              ) : (
                <>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      icon={<Download className="h-3.5 w-3.5" />}
                      loading={exporting}
                      onClick={() => void downloadPdf()}
                    >
                      Download pending PDF
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      icon={<MessageCircle className="h-3.5 w-3.5" />}
                      onClick={shareWhatsApp}
                    >
                      Share reminder on WhatsApp
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      icon={<Copy className="h-3.5 w-3.5" />}
                      onClick={() => void copyReminder()}
                    >
                      Copy reminder
                    </Button>
                  </div>
                  <p className="text-xs leading-relaxed text-slate-500">
                    WhatsApp opens with a prepared message. You control whether to send it. Attach
                    the downloaded PDF manually if you want to share the pending list. No phone
                    numbers are used, and nothing is sent automatically.
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {data.roster_available ? (
            <Card>
              <CardHeader>
                <CardTitle>Pending students</CardTitle>
                <p className="text-sm text-slate-500">
                  Only students who have not submitted are listed. This does not reveal who submitted
                  which rating or comment.
                </p>
              </CardHeader>
              <CardContent>
                {data.pending_students.length ? (
                  <Table>
                    <thead>
                      <tr>
                        <Th>USN</Th>
                        <Th>Student name</Th>
                        <Th>Status</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.pending_students.map((student) => (
                        <tr key={student.student_id}>
                          <Td className="font-medium text-slate-900">{student.student_id}</Td>
                          <Td>{student.name}</Td>
                          <Td>
                            <Badge variant="warning">Pending</Badge>
                          </Td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                ) : (
                  <EmptyState
                    title="Everyone has submitted"
                    description="All students on the verified roster have submitted feedback for this subject and period."
                    icon={<CheckCircle2 className="h-6 w-6" />}
                  />
                )}
              </CardContent>
            </Card>
          ) : null}

          <Alert variant="info" title="Privacy and scope">
            <p>{data.privacy_notice}</p>
            <p className="mt-2">{data.methodology}</p>
          </Alert>
        </>
      ) : completion.loading ? null : query ? (
        <EmptyState
          title="Completion unavailable"
          description="Select one of your active subjects to see its completion status."
        />
      ) : null}
    </div>
  );
}
