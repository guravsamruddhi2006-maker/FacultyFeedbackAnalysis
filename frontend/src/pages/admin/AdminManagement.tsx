import { useState, type FormEvent, type ReactNode } from "react";
import { Check, Pencil, Plus, Trash2, X } from "lucide-react";

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
import type { Department, FacultyMember, FeedbackPeriod, Question, StudentRow, Subject } from "@/lib/types";

type AdminSection = "faculty" | "students" | "catalog" | "audit";

function useAdminAction() {
  const { notify } = useToast();
  const [saving, setSaving] = useState(false);

  const run = async (operation: () => Promise<unknown>, successMessage: string) => {
    setSaving(true);
    try {
      await operation();
      notify(successMessage, "success");
      return true;
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The requested change could not be saved.", "error");
      return false;
    } finally {
      setSaving(false);
    }
  };

  return { run, saving };
}

function SectionCard({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        {action}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

interface PageList<T> {
  items: T[];
  total: number;
}

function FacultyManagement() {
  const faculty = useApi<PageList<FacultyMember>>("/admin/faculty?page_size=100");
  const departments = useApi<Department[]>("/catalog/departments");
  const { run, saving } = useAdminAction();
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const ok = await run(
      () => api("/admin/faculty", {
        method: "POST",
        body: {
          name: form.get("name"),
          email: form.get("email"),
          department_id: Number(form.get("department_id")),
          password: form.get("password"),
          status: "approved",
        },
      }),
      "Faculty account created.",
    );
    if (ok) {
      formElement.reset();
      setShowCreate(false);
      faculty.reload();
    }
  };

  const updateStatus = async (facultyId: number, status: "approved" | "rejected") => {
    const ok = await run(
      () => api(`/admin/faculty/${facultyId}/status`, { method: "PATCH", body: { status } }),
      `Faculty registration ${status}.`,
    );
    if (ok) faculty.reload();
  };

  const filtered = (faculty.data?.items ?? []).filter((item) =>
    `${item.name} ${item.email} ${item.department_name ?? ""} ${item.status}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Faculty management"
        description="Review registrations and manage approved faculty accounts."
        actions={<Button icon={<Plus className="h-4 w-4" />} onClick={() => setShowCreate(!showCreate)}>Add faculty</Button>}
      />
      {faculty.error ? <Alert variant="error">{faculty.error}</Alert> : null}
      {departments.error ? <Alert variant="error">{departments.error}</Alert> : null}
      {showCreate ? (
        <SectionCard title="Create faculty account">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={submit}>
            <Field label="Full name" htmlFor="faculty-name"><Input id="faculty-name" name="name" required minLength={2} /></Field>
            <Field label="Email" htmlFor="faculty-email"><Input id="faculty-email" name="email" type="email" required /></Field>
            <Field label="Department" htmlFor="faculty-department">
              <Select id="faculty-department" name="department_id" required defaultValue="">
                <option value="" disabled>Select department</option>
                {(departments.data ?? []).map((department) => (
                  <option value={department.id} key={department.id}>{department.name}</option>
                ))}
              </Select>
            </Field>
            <Field label="Temporary password" htmlFor="faculty-password"><Input id="faculty-password" name="password" type="password" required minLength={8} /></Field>
            <div className="md:col-span-2"><Button type="submit" loading={saving}>Create faculty account</Button></div>
          </form>
        </SectionCard>
      ) : null}
      <SectionCard title={`Faculty (${faculty.data?.total ?? 0})`}>
        <div className="mb-4 max-w-sm"><Input aria-label="Search faculty" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, email or status" /></div>
        {faculty.loading ? <LoadingBlock label="Loading faculty…" /> : filtered.length ? (
          <Table>
            <thead><tr><Th>Name</Th><Th>Department</Th><Th>Status</Th><Th>Offerings</Th><Th>Responses</Th><Th className="text-right">Actions</Th></tr></thead>
            <tbody>{filtered.map((item) => (
              <tr key={item.faculty_id}>
                <Td><p className="font-medium">{item.name}</p><p className="text-xs text-slate-500">{item.email}</p></Td>
                <Td>{item.department_name}</Td>
                <Td><Badge variant={item.status === "approved" ? "success" : item.status === "pending" ? "warning" : "outline"}>{item.status}</Badge></Td>
                <Td>{item.offering_count ?? 0}</Td>
                <Td>{item.response_count ?? 0}</Td>
                <Td className="text-right">
                  <div className="flex justify-end gap-2">
                    {item.status !== "approved" ? <Button size="sm" loading={saving} onClick={() => void updateStatus(item.faculty_id, "approved")} icon={<Check className="h-3.5 w-3.5" />}>{item.status === "pending" ? "Approve" : "Reactivate"}</Button> : null}
                    {item.status === "pending" ? <Button size="sm" variant="outline" loading={saving} onClick={() => void updateStatus(item.faculty_id, "rejected")} icon={<X className="h-3.5 w-3.5" />}>Reject</Button> : null}
                    {item.status === "approved" ? <Button size="sm" variant="outline" loading={saving} onClick={() => void run(
                      () => api(`/admin/faculty/${item.faculty_id}/status`, { method: "PATCH", body: { status: "inactive" } }),
                      "Faculty account deactivated.",
                    ).then((ok) => { if (ok) faculty.reload(); })}>Deactivate</Button> : null}
                  </div>
                </Td>
              </tr>
            ))}</tbody>
          </Table>
        ) : <EmptyState title="No faculty accounts found" description="Try another search or add a faculty account." />}
      </SectionCard>
    </div>
  );
}

function StudentManagement() {
  const students = useApi<PageList<StudentRow>>("/admin/students?page_size=100");
  const departments = useApi<Department[]>("/catalog/departments");
  const [selectedStudent, setSelectedStudent] = useState<string | null>(null);
  const [editingStudent, setEditingStudent] = useState<StudentRow | null>(null);
  const studentDetails = useApi<{
    student_id: string;
    name: string;
    department_name: string;
    submissions: Array<{
      feedback_id: number;
      submitted_at: string;
      academic_year: string;
      semester_number: number;
      subject_code: string;
      subject_name: string;
      faculty_name: string;
    }>;
    audit_notice: string;
  }>(selectedStudent ? `/admin/students/${encodeURIComponent(selectedStudent)}` : null);
  const { run, saving } = useAdminAction();
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const ok = await run(
      () => api("/admin/students", {
        method: "POST",
        body: {
          student_id: form.get("student_id"),
          name: form.get("name"),
          department_id: Number(form.get("department_id")),
          password: form.get("password"),
        },
      }),
      "Student account created.",
    );
    if (ok) {
      formElement.reset();
      setShowCreate(false);
      students.reload();
    }
  };

  const submitEdit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingStudent) return;
    const form = new FormData(event.currentTarget);
    const ok = await run(
      () => api(`/admin/students/${encodeURIComponent(editingStudent.student_id)}`, {
        method: "PATCH",
        body: {
          name: form.get("name"),
          department_id: Number(form.get("department_id")),
        },
      }),
      "Student account updated.",
    );
    if (ok) {
      setEditingStudent(null);
      students.reload();
    }
  };

  const filtered = (students.data?.items ?? []).filter((item) =>
    `${item.name} ${item.student_id} ${item.department_name ?? ""}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student management"
        description="Review student account and aggregate submission counts. Student-linked feedback is not shown here."
        actions={<Button icon={<Plus className="h-4 w-4" />} onClick={() => setShowCreate(!showCreate)}>Add student</Button>}
      />
      {students.error ? <Alert variant="error">{students.error}</Alert> : null}
      {departments.error ? <Alert variant="error">{departments.error}</Alert> : null}
      {selectedStudent ? (
        <SectionCard
          title={`Submission history · ${studentDetails.data?.name ?? selectedStudent}`}
          action={<Button variant="ghost" size="sm" onClick={() => setSelectedStudent(null)}>Close</Button>}
        >
          {studentDetails.loading ? <LoadingBlock label="Loading audited student details…" /> : studentDetails.error ? (
            <Alert variant="error">{studentDetails.error}</Alert>
          ) : studentDetails.data ? (
            <div className="space-y-4">
              <Alert variant="warning">{studentDetails.data.audit_notice} This view contains submission metadata only, not feedback text or ratings.</Alert>
              <p className="text-sm text-slate-600">{studentDetails.data.student_id} · {studentDetails.data.department_name}</p>
              {studentDetails.data.submissions.length ? (
                <Table>
                  <thead><tr><Th>Subject</Th><Th>Faculty</Th><Th>Academic year</Th><Th>Submitted</Th></tr></thead>
                  <tbody>{studentDetails.data.submissions.map((submission) => (
                    <tr key={submission.feedback_id}>
                      <Td>{submission.subject_code} · {submission.subject_name}</Td>
                      <Td>{submission.faculty_name}</Td>
                      <Td>{submission.academic_year} · Semester {submission.semester_number}</Td>
                      <Td>{new Date(submission.submitted_at).toLocaleString()}</Td>
                    </tr>
                  ))}</tbody>
                </Table>
              ) : <EmptyState title="No submissions recorded" />}
            </div>
          ) : null}
        </SectionCard>
      ) : null}
      {showCreate ? (
        <SectionCard title="Create student account">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={submit}>
            <Field label="Student ID / USN" htmlFor="student-id"><Input id="student-id" name="student_id" required minLength={6} /></Field>
            <Field label="Full name" htmlFor="student-name"><Input id="student-name" name="name" required minLength={2} /></Field>
            <Field label="Department" htmlFor="student-department">
              <Select id="student-department" name="department_id" required defaultValue="">
                <option value="" disabled>Select department</option>
                {(departments.data ?? []).map((department) => (
                  <option value={department.id} key={department.id}>{department.name}</option>
                ))}
              </Select>
            </Field>
            <Field label="Temporary password" htmlFor="student-password"><Input id="student-password" name="password" type="password" required minLength={8} /></Field>
            <div className="md:col-span-2"><Button type="submit" loading={saving}>Create student account</Button></div>
          </form>
        </SectionCard>
      ) : null}
      {editingStudent ? (
        <SectionCard title={`Edit student · ${editingStudent.student_id}`}>
          <form className="grid gap-4 md:grid-cols-2" onSubmit={submitEdit}>
            <Field label="Full name" htmlFor="edit-student-name"><Input id="edit-student-name" name="name" required minLength={2} defaultValue={editingStudent.name} /></Field>
            <Field label="Department" htmlFor="edit-student-department">
              <Select id="edit-student-department" name="department_id" required defaultValue={editingStudent.department_id}>
                {(departments.data ?? []).map((department) => (
                  <option value={department.id} key={department.id}>{department.name}</option>
                ))}
              </Select>
            </Field>
            <div className="flex gap-2 md:col-span-2"><Button type="submit" loading={saving}>Save student</Button><Button type="button" variant="ghost" onClick={() => setEditingStudent(null)}>Cancel</Button></div>
          </form>
        </SectionCard>
      ) : null}
      <SectionCard title={`Students (${students.data?.total ?? 0})`}>
        <div className="mb-4 max-w-sm"><Input aria-label="Search students" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search student ID, name or department" /></div>
        {students.loading ? <LoadingBlock label="Loading students…" /> : filtered.length ? (
          <Table>
            <thead><tr><Th>Student ID</Th><Th>Name</Th><Th>Department</Th><Th>Submissions</Th><Th className="text-right">Actions</Th></tr></thead>
            <tbody>{filtered.map((item) => (
              <tr key={item.student_id}>
                <Td>{item.student_id}</Td><Td>{item.name}</Td><Td>{item.department_name}</Td><Td>{item.feedback_count ?? 0}</Td>
                <Td><div className="flex justify-end gap-2"><Button size="sm" variant="outline" onClick={() => setEditingStudent(item)} icon={<Pencil className="h-3.5 w-3.5" />}>Edit</Button><Button size="sm" variant="outline" onClick={() => setSelectedStudent(item.student_id)}>View submissions</Button></div></Td>
              </tr>
            ))}</tbody>
          </Table>
        ) : <EmptyState title="No students found" description="Try another search or create a student account." />}
      </SectionCard>
    </div>
  );
}

function SubjectManagement() {
  const subjects = useApi<Subject[]>("/catalog/subjects");
  const { run, saving } = useAdminAction();
  const [editing, setEditing] = useState<Subject | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      subject_code: String(form.get("subject_code")).trim().toUpperCase(),
      subject_name: String(form.get("subject_name")).trim(),
      semester_number: Number(form.get("semester_number")),
    };
    const ok = await run(
      () => api(editing ? `/catalog/subjects/${encodeURIComponent(editing.subject_code)}` : "/catalog/subjects", {
        method: editing ? "PUT" : "POST",
        body: payload,
      }),
      editing ? "Subject updated." : "Subject created.",
    );
    if (ok) {
      setEditing(null);
      formElement.reset();
      subjects.reload();
    }
  };

  const remove = async (code: string) => {
    if (!window.confirm(`Delete subject ${code}? Subjects used by offerings cannot be deleted.`)) return;
    const ok = await run(() => api(`/catalog/subjects/${encodeURIComponent(code)}`, { method: "DELETE" }), "Subject deleted.");
    if (ok) subjects.reload();
  };

  return (
    <div className="space-y-5">
      <form key={editing?.subject_code ?? "new-subject"} className="grid gap-3 rounded-lg border p-4 md:grid-cols-[1fr_2fr_160px_auto]" onSubmit={submit}>
        <Field label="Subject code" htmlFor="subject-code"><Input id="subject-code" name="subject_code" required defaultValue={editing?.subject_code ?? ""} readOnly={Boolean(editing)} /></Field>
        <Field label="Subject name" htmlFor="subject-name"><Input id="subject-name" name="subject_name" required minLength={3} defaultValue={editing?.subject_name ?? ""} /></Field>
        <Field label="Semester" htmlFor="subject-semester"><Input id="subject-semester" name="semester_number" type="number" min={1} max={8} required defaultValue={editing?.semester_number ?? ""} /></Field>
        <div className="flex items-end gap-2"><Button type="submit" loading={saving}>{editing ? "Save" : "Add"}</Button>{editing ? <Button type="button" variant="ghost" onClick={() => setEditing(null)}>Cancel</Button> : null}</div>
      </form>
      {subjects.error ? <Alert variant="error">{subjects.error}</Alert> : null}
      {subjects.loading ? <LoadingBlock /> : subjects.data?.length ? (
        <Table>
          <thead><tr><Th>Code</Th><Th>Subject</Th><Th>Semester</Th><Th className="text-right">Actions</Th></tr></thead>
          <tbody>{subjects.data.map((subject) => (
            <tr key={subject.subject_code}>
              <Td>{subject.subject_code}</Td><Td>{subject.subject_name}</Td><Td>{subject.semester_number}</Td>
              <Td className="text-right"><div className="flex justify-end gap-2"><Button size="sm" variant="outline" onClick={() => setEditing(subject)} icon={<Pencil className="h-3.5 w-3.5" />}>Edit</Button><Button size="sm" variant="ghost" onClick={() => void remove(subject.subject_code)} icon={<Trash2 className="h-3.5 w-3.5" />}>Delete</Button></div></Td>
            </tr>
          ))}</tbody>
        </Table>
      ) : <EmptyState title="No subjects configured" />}
    </div>
  );
}

function AcademicYearManagement() {
  const years = useApi<Array<{ academic_year: string }>>("/catalog/academic-years");
  const { run, saving } = useAdminAction();

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const ok = await run(() => api("/catalog/academic-years", {
      method: "POST",
      body: { academic_year: form.get("academic_year") },
    }), "Academic year added.");
    if (ok) {
      formElement.reset();
      years.reload();
    }
  };

  const remove = async (year: string) => {
    if (!window.confirm(`Remove academic year ${year}? Years with course offerings are preserved.`)) return;
    const ok = await run(() => api(`/catalog/academic-years/${encodeURIComponent(year)}`, { method: "DELETE" }), "Academic year removed.");
    if (ok) years.reload();
  };

  return (
    <div className="space-y-5">
      <form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={submit}>
        <Field label="Academic year (e.g. 2027-28)" htmlFor="academic-year"><Input id="academic-year" name="academic_year" pattern="[0-9]{4}-[0-9]{2}" required /></Field>
        <Button type="submit" loading={saving}>Add academic year</Button>
      </form>
      {years.error ? <Alert variant="error">{years.error}</Alert> : null}
      {years.loading ? <LoadingBlock /> : years.data?.length ? (
        <div className="divide-y rounded-lg border">
          {years.data.map(({ academic_year }) => (
            <div className="flex items-center justify-between p-3" key={academic_year}>
              <span className="font-medium">{academic_year}</span>
              <Button size="sm" variant="ghost" onClick={() => void remove(academic_year)} icon={<Trash2 className="h-3.5 w-3.5" />}>Remove</Button>
            </div>
          ))}
        </div>
      ) : <EmptyState title="No academic years configured" />}
    </div>
  );
}

interface OfferingRow {
  offering_id: number;
  academic_year: string;
  semester_number: number;
  subject_code: string;
  subject_name: string;
  faculty_id: number;
  faculty_name: string;
  period_open: boolean;
}

function OfferingManagement() {
  const offerings = useApi<PageList<OfferingRow>>("/catalog/course-offerings?page_size=100");
  const subjects = useApi<Subject[]>("/catalog/subjects");
  const years = useApi<Array<{ academic_year: string }>>("/catalog/academic-years");
  const faculty = useApi<PageList<FacultyMember>>("/admin/faculty?status=approved&page_size=100");
  const semesters = useApi<Array<{ semester_number: number }>>("/catalog/semesters");
  const { run, saving } = useAdminAction();

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const ok = await run(() => api("/catalog/course-offerings", {
      method: "POST",
      body: {
        academic_year: form.get("academic_year"),
        semester_number: Number(form.get("semester_number")),
        subject_code: form.get("subject_code"),
        faculty_id: Number(form.get("faculty_id")),
      },
    }), "Course offering assigned.");
    if (ok) {
      formElement.reset();
      offerings.reload();
    }
  };

  const remove = async (offering: OfferingRow) => {
    if (!window.confirm(`Remove ${offering.subject_code} assigned to ${offering.faculty_name}? Existing feedback prevents removal.`)) return;
    const ok = await run(() => api(`/catalog/course-offerings/${offering.offering_id}`, { method: "DELETE" }), "Course offering removed.");
    if (ok) offerings.reload();
  };

  return (
    <div className="space-y-5">
      <form className="grid gap-3 rounded-lg border p-4 md:grid-cols-2 xl:grid-cols-4" onSubmit={submit}>
        <Field label="Academic year" htmlFor="offering-year">
          <Select id="offering-year" name="academic_year" defaultValue="" required><option value="" disabled>Select year</option>{(years.data ?? []).map((item) => <option key={item.academic_year}>{item.academic_year}</option>)}</Select>
        </Field>
        <Field label="Semester" htmlFor="offering-semester">
          <Select id="offering-semester" name="semester_number" defaultValue="" required><option value="" disabled>Select semester</option>{(semesters.data ?? []).map((item) => <option key={item.semester_number} value={item.semester_number}>{item.semester_number}</option>)}</Select>
        </Field>
        <Field label="Subject" htmlFor="offering-subject">
          <Select id="offering-subject" name="subject_code" defaultValue="" required><option value="" disabled>Select subject</option>{(subjects.data ?? []).map((item) => <option key={item.subject_code} value={item.subject_code}>{item.subject_code} · {item.subject_name}</option>)}</Select>
        </Field>
        <Field label="Approved faculty" htmlFor="offering-faculty">
          <Select id="offering-faculty" name="faculty_id" defaultValue="" required><option value="" disabled>Select faculty</option>{(faculty.data?.items ?? []).map((item) => <option key={item.faculty_id} value={item.faculty_id}>{item.name}</option>)}</Select>
        </Field>
        <div className="xl:col-span-4"><Button type="submit" loading={saving}>Assign course offering</Button></div>
      </form>
      {[offerings, subjects, years, faculty, semesters].some((item) => item.error) ? <Alert variant="error">Some course-offering options could not be loaded. Refresh the page and try again.</Alert> : null}
      {offerings.loading ? <LoadingBlock /> : offerings.data?.items.length ? (
        <Table>
          <thead><tr><Th>Academic year</Th><Th>Semester</Th><Th>Subject</Th><Th>Faculty</Th><Th>Feedback period</Th><Th /></tr></thead>
          <tbody>{offerings.data.items.map((item) => (
            <tr key={item.offering_id}>
              <Td>{item.academic_year}</Td><Td>{item.semester_number}</Td><Td>{item.subject_code} · {item.subject_name}</Td><Td>{item.faculty_name}</Td><Td><Badge variant={item.period_open ? "success" : "outline"}>{item.period_open ? "Open" : "Closed"}</Badge></Td><Td><Button size="sm" variant="ghost" onClick={() => void remove(item)} icon={<Trash2 className="h-3.5 w-3.5" />}>Remove</Button></Td>
            </tr>
          ))}</tbody>
        </Table>
      ) : <EmptyState title="No course offerings configured" />}
    </div>
  );
}

function FeedbackPeriodManagement() {
  const periods = useApi<FeedbackPeriod[]>("/catalog/feedback-periods");
  const years = useApi<Array<{ academic_year: string }>>("/catalog/academic-years");
  const semesters = useApi<Array<{ semester_number: number }>>("/catalog/semesters");
  const { run, saving } = useAdminAction();

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const ok = await run(() => api("/catalog/feedback-periods", {
      method: "PUT",
      body: {
        academic_year: form.get("academic_year"),
        semester_number: Number(form.get("semester_number")),
        start_date: new Date(String(form.get("start_date"))).toISOString(),
        end_date: new Date(String(form.get("end_date"))).toISOString(),
      },
    }), "Feedback period saved.");
    if (ok) {
      formElement.reset();
      periods.reload();
    }
  };

  const remove = async (period: FeedbackPeriod) => {
    if (!window.confirm(`Remove the feedback period for ${period.academic_year}, semester ${period.semester_number}?`)) return;
    const ok = await run(() => api(`/catalog/feedback-periods/${encodeURIComponent(period.academic_year)}/${period.semester_number}`, { method: "DELETE" }), "Feedback period removed.");
    if (ok) periods.reload();
  };

  return (
    <div className="space-y-5">
      <form className="grid gap-3 rounded-lg border p-4 md:grid-cols-2 xl:grid-cols-4" onSubmit={submit}>
        <Field label="Academic year" htmlFor="period-year"><Select id="period-year" name="academic_year" defaultValue="" required><option value="" disabled>Select year</option>{(years.data ?? []).map((item) => <option key={item.academic_year}>{item.academic_year}</option>)}</Select></Field>
        <Field label="Semester" htmlFor="period-semester"><Select id="period-semester" name="semester_number" defaultValue="" required><option value="" disabled>Select semester</option>{(semesters.data ?? []).map((item) => <option key={item.semester_number} value={item.semester_number}>{item.semester_number}</option>)}</Select></Field>
        <Field label="Starts" htmlFor="period-start"><Input id="period-start" name="start_date" type="datetime-local" required /></Field>
        <Field label="Ends" htmlFor="period-end"><Input id="period-end" name="end_date" type="datetime-local" required /></Field>
        <div className="xl:col-span-4"><Button type="submit" loading={saving}>Save feedback period</Button></div>
      </form>
      {[years, semesters].some((item) => item.error) ? <Alert variant="error">Academic year or semester options could not be loaded.</Alert> : null}
      {periods.error ? <Alert variant="error">{periods.error}</Alert> : null}
      {periods.loading ? <LoadingBlock /> : periods.data?.length ? (
        <Table>
          <thead><tr><Th>Academic year</Th><Th>Semester</Th><Th>Starts</Th><Th>Ends</Th><Th>Status</Th><Th /></tr></thead>
          <tbody>{periods.data.map((period) => (
            <tr key={`${period.academic_year}-${period.semester_number}`}>
              <Td>{period.academic_year}</Td><Td>{period.semester_number}</Td><Td>{new Date(period.start_date).toLocaleString()}</Td><Td>{new Date(period.end_date).toLocaleString()}</Td><Td><Badge variant={period.is_open ? "success" : "outline"}>{period.is_open ? "Open" : "Closed"}</Badge></Td><Td><Button size="sm" variant="ghost" onClick={() => void remove(period)} icon={<Trash2 className="h-3.5 w-3.5" />}>Remove</Button></Td>
            </tr>
          ))}</tbody>
        </Table>
      ) : <EmptyState title="No feedback periods configured" />}
    </div>
  );
}

function FeedbackQuestionManagement() {
  const questions = useApi<Question[]>("/catalog/feedback-questions?include_inactive=true");
  const { run, saving } = useAdminAction();
  const [editing, setEditing] = useState<Question | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = { question_text: String(form.get("question_text")).trim(), is_active: form.get("is_active") === "on" };
    const ok = await run(
      () => api(editing ? `/catalog/feedback-questions/${editing.question_id}` : "/catalog/feedback-questions", {
        method: editing ? "PUT" : "POST",
        body: payload,
      }),
      editing ? "Feedback question updated." : "Feedback question added.",
    );
    if (ok) {
      setEditing(null);
      formElement.reset();
      questions.reload();
    }
  };

  const remove = async (question: Question) => {
    if (!window.confirm("Delete this feedback question? Questions with existing answers cannot be deleted; deactivate instead.")) return;
    const ok = await run(() => api(`/catalog/feedback-questions/${question.question_id}`, { method: "DELETE" }), "Feedback question deleted.");
    if (ok) questions.reload();
  };

  return (
    <div className="space-y-5">
      <form key={editing?.question_id ?? "new-question"} className="space-y-3 rounded-lg border p-4" onSubmit={submit}>
        <Field label="Question text" htmlFor="question-text"><Textarea id="question-text" name="question_text" required minLength={5} maxLength={500} defaultValue={editing?.question_text ?? ""} /></Field>
        <label className="flex items-center gap-2 text-sm text-slate-700"><input name="is_active" type="checkbox" defaultChecked={editing?.is_active ?? true} /> Active for new submissions</label>
        <div className="flex gap-2"><Button type="submit" loading={saving}>{editing ? "Save question" : "Add question"}</Button>{editing ? <Button type="button" variant="ghost" onClick={() => setEditing(null)}>Cancel</Button> : null}</div>
      </form>
      {questions.error ? <Alert variant="error">{questions.error}</Alert> : null}
      {questions.loading ? <LoadingBlock /> : questions.data?.length ? (
        <div className="divide-y rounded-lg border">
          {questions.data.map((question) => (
            <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between" key={question.question_id}>
              <div><p className="text-sm text-slate-800">{question.question_text}</p><Badge variant={question.is_active ? "success" : "outline"}>{question.is_active ? "Active" : "Inactive"}</Badge></div>
              <div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => setEditing(question)} icon={<Pencil className="h-3.5 w-3.5" />}>Edit</Button><Button size="sm" variant="ghost" onClick={() => void remove(question)} icon={<Trash2 className="h-3.5 w-3.5" />}>Delete</Button></div>
            </div>
          ))}
        </div>
      ) : <EmptyState title="No feedback questions configured" />}
    </div>
  );
}

function CatalogManagement() {
  const [tab, setTab] = useState<"subjects" | "offerings" | "years" | "periods" | "questions">("subjects");
  const tabs: Array<{ id: typeof tab; label: string }> = [
    { id: "subjects", label: "Subjects" },
    { id: "offerings", label: "Course offerings" },
    { id: "years", label: "Academic years" },
    { id: "periods", label: "Feedback periods" },
    { id: "questions", label: "Feedback questions" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Catalog management" description="Manage the department catalog and feedback schedule." />
      <div className="flex gap-2 overflow-x-auto border-b pb-2">
        {tabs.map((item) => (
          <Button key={item.id} variant={tab === item.id ? "secondary" : "ghost"} size="sm" onClick={() => setTab(item.id)}>{item.label}</Button>
        ))}
      </div>
      {tab === "subjects" ? <SectionCard title="Subjects"><SubjectManagement /></SectionCard> : null}
      {tab === "offerings" ? <SectionCard title="Course offerings"><OfferingManagement /></SectionCard> : null}
      {tab === "years" ? <SectionCard title="Academic years"><AcademicYearManagement /></SectionCard> : null}
      {tab === "periods" ? <SectionCard title="Feedback periods"><FeedbackPeriodManagement /></SectionCard> : null}
      {tab === "questions" ? <SectionCard title="Feedback questions"><FeedbackQuestionManagement /></SectionCard> : null}
    </div>
  );
}

interface AuditLog {
  log_id: number;
  actor_role: string;
  actor_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  created_at: string;
}

function AuditManagement() {
  const logs = useApi<PageList<AuditLog>>("/admin/audit-logs?page_size=100");
  return (
    <div className="space-y-6">
      <PageHeader title="Audit log" description="Administrative actions are recorded for accountability." />
      {logs.error ? <Alert variant="error">{logs.error}</Alert> : null}
      <SectionCard title={`Recent events (${logs.data?.total ?? 0})`}>
        {logs.loading ? <LoadingBlock /> : logs.data?.items.length ? (
          <Table>
            <thead><tr><Th>Time</Th><Th>Actor</Th><Th>Action</Th><Th>Entity</Th><Th>Entity ID</Th></tr></thead>
            <tbody>{logs.data.items.map((item) => (
              <tr key={item.log_id}><Td>{new Date(item.created_at).toLocaleString()}</Td><Td>{item.actor_role} · {item.actor_id}</Td><Td>{item.action}</Td><Td>{item.entity_type}</Td><Td>{item.entity_id}</Td></tr>
            ))}</tbody>
          </Table>
        ) : <EmptyState title="No audit events" />}
      </SectionCard>
    </div>
  );
}

export function AdminManagement({ section }: { section: AdminSection }) {
  if (section === "faculty") return <FacultyManagement />;
  if (section === "students") return <StudentManagement />;
  if (section === "catalog") return <CatalogManagement />;
  return <AuditManagement />;
}
