import { useEffect, useMemo, useState } from "react";
import { ClipboardCheck, Plus, Trash2, UserPlus, Users } from "lucide-react";

import {
  Alert,
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  Field,
  Input,
  LoadingBlock,
  PageHeader,
  Select,
  Table,
  Td,
  Textarea,
  Th,
} from "@/components/ui";
import { useToast } from "@/context/ToastContext";
import { useApi } from "@/hooks/useApi";
import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type {
  EnrollmentBulkResult,
  EnrollmentListResponse,
  Subject,
} from "@/lib/types";

interface YearRow {
  academic_year: string;
}

interface SemesterRow {
  semester_number: number;
}

export function AdminRostersPage() {
  const { notify } = useToast();
  const years = useApi<YearRow[]>("/catalog/academic-years");
  const semesters = useApi<SemesterRow[]>("/catalog/semesters");
  const subjects = useApi<Subject[]>("/catalog/subjects");

  const [academicYear, setAcademicYear] = useState("");
  const [semesterNumber, setSemesterNumber] = useState("");
  const [subjectCode, setSubjectCode] = useState("");
  const [studentId, setStudentId] = useState("");
  const [bulkText, setBulkText] = useState("");
  const [saving, setSaving] = useState(false);
  const [bulkSaving, setBulkSaving] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);
  const [bulkResult, setBulkResult] = useState<EnrollmentBulkResult | null>(null);

  useEffect(() => {
    if (academicYear || !years.data?.length) return;
    const firstSubject = subjects.data?.[0];
    const semester =
      firstSubject?.semester_number ??
      semesters.data?.find((row) => row.semester_number === 5)?.semester_number ??
      semesters.data?.[0]?.semester_number ??
      5;
    const subject =
      subjects.data?.find((row) => row.semester_number === semester) ?? firstSubject;
    setAcademicYear(years.data[0].academic_year);
    setSemesterNumber(String(semester));
    setSubjectCode(subject?.subject_code ?? "");
  }, [academicYear, years.data, semesters.data, subjects.data]);

  useEffect(() => {
    if (!academicYear || !semesterNumber || subjectCode) return;
    const match = subjects.data?.find(
      (row) => row.semester_number === Number(semesterNumber),
    );
    if (match) setSubjectCode(match.subject_code);
  }, [academicYear, semesterNumber, subjectCode, subjects.data]);

  const subjectOptions = useMemo(
    () =>
      (subjects.data ?? []).filter(
        (row) => row.semester_number === Number(semesterNumber),
      ),
    [subjects.data, semesterNumber],
  );

  const rosterQuery = useMemo(() => {
    if (!academicYear || !semesterNumber || !subjectCode) return null;
    const params = new URLSearchParams({
      academic_year: academicYear,
      semester_number: semesterNumber,
      subject_code: subjectCode,
    });
    return `/admin/enrollments?${params.toString()}`;
  }, [academicYear, semesterNumber, subjectCode]);

  const roster = useApi<EnrollmentListResponse>(rosterQuery);
  const data = roster.data;

  const changeSemester = (value: string) => {
    const match = (subjects.data ?? []).find(
      (row) => row.semester_number === Number(value),
    );
    setSemesterNumber(value);
    setSubjectCode(match?.subject_code ?? "");
  };

  const addStudent = async () => {
    const id = studentId.trim().toUpperCase();
    if (!id || !academicYear || !semesterNumber || !subjectCode) return;
    setSaving(true);
    try {
      const result = await api<{ message: string; created: boolean }>("/admin/enrollments", {
        method: "POST",
        body: {
          student_id: id,
          subject_code: subjectCode,
          academic_year: academicYear,
          semester_number: Number(semesterNumber),
        },
      });
      notify(result.message, result.created ? "success" : "info");
      setStudentId("");
      roster.reload();
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The student could not be added.", "error");
    } finally {
      setSaving(false);
    }
  };

  const addBulk = async () => {
    const ids = Array.from(
      new Set(
        bulkText
          .split(/[\s,;]+/)
          .map((value) => value.trim().toUpperCase())
          .filter(Boolean),
      ),
    );
    if (!ids.length || !academicYear || !semesterNumber || !subjectCode) return;
    setBulkSaving(true);
    setBulkResult(null);
    try {
      const result = await api<EnrollmentBulkResult>("/admin/enrollments/bulk", {
        method: "POST",
        body: {
          student_ids: ids,
          subject_code: subjectCode,
          academic_year: academicYear,
          semester_number: Number(semesterNumber),
        },
      });
      setBulkResult(result);
      notify(result.message, "success");
      setBulkText("");
      roster.reload();
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The roster could not be updated.", "error");
    } finally {
      setBulkSaving(false);
    }
  };

  const removeStudent = async (enrollmentId: number, usn: string) => {
    if (
      !window.confirm(
        `Remove ${usn} from this roster? This does not delete any feedback they already submitted.`,
      )
    ) {
      return;
    }
    setRemovingId(enrollmentId);
    try {
      const result = await api<{ message: string }>(`/admin/enrollments/${enrollmentId}`, {
        method: "DELETE",
      });
      notify(result.message, "success");
      roster.reload();
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The roster entry could not be removed.", "error");
    } finally {
      setRemovingId(null);
    }
  };

  const loadingOptions = (years.loading && !years.data) || (subjects.loading && !subjects.data);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Class rosters"
        description="Verified rosters power faculty completion tracking. Only students added here count as eligible; feedback content stays anonymous."
      />

      {years.error ? <Alert variant="error">{years.error}</Alert> : null}
      {semesters.error ? <Alert variant="error">{semesters.error}</Alert> : null}
      {subjects.error ? <Alert variant="error">{subjects.error}</Alert> : null}
      {roster.error ? <Alert variant="error">{roster.error}</Alert> : null}

      {loadingOptions ? (
        <LoadingBlock label="Loading catalog…" />
      ) : !(subjects.data ?? []).length ? (
        <EmptyState
          title="No subjects in the catalog"
          description="Add subjects under Catalog before creating a class roster."
          icon={<ClipboardCheck className="h-6 w-6" />}
        />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Choose a class</CardTitle>
              <p className="text-sm text-slate-500">
                A roster belongs to one subject in one academic year and semester.
              </p>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-3">
              <Select
                aria-label="Academic year"
                value={academicYear}
                onChange={(event) => setAcademicYear(event.target.value)}
              >
                {(years.data ?? []).map((row) => (
                  <option key={row.academic_year} value={row.academic_year}>
                    {row.academic_year}
                  </option>
                ))}
              </Select>
              <Select
                aria-label="Semester"
                value={semesterNumber}
                onChange={(event) => changeSemester(event.target.value)}
              >
                {(semesters.data ?? []).map((row) => (
                  <option key={row.semester_number} value={row.semester_number}>
                    Semester {row.semester_number}
                  </option>
                ))}
              </Select>
              <Select
                aria-label="Subject"
                value={subjectCode}
                onChange={(event) => setSubjectCode(event.target.value)}
              >
                {subjectOptions.length ? (
                  subjectOptions.map((row) => (
                    <option key={row.subject_code} value={row.subject_code}>
                      {row.subject_code} — {row.subject_name}
                    </option>
                  ))
                ) : (
                  <option value="">No subjects in this semester</option>
                )}
              </Select>
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Add one student</CardTitle>
                <p className="text-sm text-slate-500">
                  The USN must belong to an existing, active student account.
                </p>
              </CardHeader>
              <CardContent className="space-y-3">
                <Field label="Student USN" htmlFor="roster-usn" hint="Example: 4UB26CS001">
                  <Input
                    id="roster-usn"
                    value={studentId}
                    onChange={(event) => setStudentId(event.target.value)}
                    placeholder="Enter a USN"
                    autoComplete="off"
                  />
                </Field>
                <Button
                  icon={<UserPlus className="h-4 w-4" />}
                  loading={saving}
                  disabled={!studentId.trim() || !subjectCode}
                  onClick={() => void addStudent()}
                >
                  Add to roster
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Add several students</CardTitle>
                <p className="text-sm text-slate-500">
                  Paste USNs separated by commas, spaces or new lines. Unknown and archived
                  accounts are reported, never silently added.
                </p>
              </CardHeader>
              <CardContent className="space-y-3">
                <Field label="Student USNs" htmlFor="roster-bulk">
                  <Textarea
                    id="roster-bulk"
                    value={bulkText}
                    onChange={(event) => setBulkText(event.target.value)}
                    placeholder={"4UB26CS001\n4UB26CS002\n4UB26CS003"}
                  />
                </Field>
                <Button
                  icon={<Plus className="h-4 w-4" />}
                  loading={bulkSaving}
                  disabled={!bulkText.trim() || !subjectCode}
                  onClick={() => void addBulk()}
                >
                  Add all to roster
                </Button>
              </CardContent>
            </Card>
          </div>

          {bulkResult ? (
            <Alert
              variant={bulkResult.unknown.length || bulkResult.inactive.length ? "warning" : "success"}
              title={bulkResult.message}
            >
              {bulkResult.skipped_existing ? (
                <p>{bulkResult.skipped_existing} already on this roster.</p>
              ) : null}
              {bulkResult.unknown.length ? (
                <p>Unknown USNs: {bulkResult.unknown.join(", ")}</p>
              ) : null}
              {bulkResult.inactive.length ? (
                <p>Archived accounts: {bulkResult.inactive.join(", ")}</p>
              ) : null}
            </Alert>
          ) : null}

          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <CardTitle>Verified roster</CardTitle>
                  <p className="mt-1 text-sm text-slate-500">
                    {data
                      ? `${data.scope.subject_code} — ${data.scope.subject_name} · ${data.scope.academic_year} · Semester ${data.scope.semester_number}`
                      : "Select a class to view its roster."}
                  </p>
                </div>
                <Badge variant="info">
                  <Users className="mr-1 h-3.5 w-3.5" />
                  {data?.total ?? 0} student{(data?.total ?? 0) === 1 ? "" : "s"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {roster.loading && !data ? (
                <LoadingBlock label="Loading the verified roster…" />
              ) : data?.items.length ? (
                <Table>
                  <thead>
                    <tr>
                      <Th>USN</Th>
                      <Th>Student name</Th>
                      <Th>Department</Th>
                      <Th>Added</Th>
                      <Th>Account</Th>
                      <Th className="text-right">Action</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((item) => (
                      <tr key={item.enrollment_id}>
                        <Td className="font-medium text-slate-900">{item.student_id}</Td>
                        <Td>{item.name}</Td>
                        <Td>{item.department_name}</Td>
                        <Td>{formatDate(item.created_at)}</Td>
                        <Td>
                          <Badge variant={item.is_active ? "success" : "outline"}>
                            {item.is_active ? "Active" : "Archived"}
                          </Badge>
                        </Td>
                        <Td className="text-right">
                          <Button
                            size="sm"
                            variant="ghost"
                            loading={removingId === item.enrollment_id}
                            icon={<Trash2 className="h-3.5 w-3.5" />}
                            onClick={() => void removeStudent(item.enrollment_id, item.student_id)}
                          >
                            Remove
                          </Button>
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : (
                <EmptyState
                  title="No verified students yet"
                  description="Add USNs above to build this class roster. Faculty cannot calculate completion until at least one active student is enrolled."
                  icon={<ClipboardCheck className="h-6 w-6" />}
                />
              )}
              {data?.methodology ? (
                <p className="mt-4 text-xs leading-relaxed text-slate-500">{data.methodology}</p>
              ) : null}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
