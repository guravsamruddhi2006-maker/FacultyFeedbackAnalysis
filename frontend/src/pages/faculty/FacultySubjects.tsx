import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, BookOpen, Pencil, Plus, Send, Trash2 } from "lucide-react";

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
  Modal,
  PageHeader,
  Select,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import type { FacultySelection, Subject, SubjectRequest } from "@/lib/types";

interface SelectionForm {
  subject_code: string;
  academic_year: string;
  semester_number: string;
}

function subjectSemester(subjects: Subject[], code: string): string {
  const subject = subjects.find((item) => item.subject_code === code);
  return subject ? String(subject.semester_number) : "";
}

export function FacultySubjectsPage() {
  const subjects = useApi<Subject[]>("/catalog/subjects");
  const years = useApi<Array<{ academic_year: string }>>("/catalog/academic-years");
  const semesters = useApi<Array<{ semester_number: number }>>("/catalog/semesters");
  const selections = useApi<FacultySelection[]>("/faculty/me/selections");
  const requests = useApi<SubjectRequest[]>("/faculty/me/subject-requests");
  const { notify } = useToast();

  const yearOptions = [...(years.data ?? [])].sort((a, b) => a.academic_year.localeCompare(b.academic_year));
  const semesterOptions = (
    semesters.data?.length
      ? semesters.data.map((item) => item.semester_number)
      : Array.from({ length: 8 }, (_, index) => index + 1)
  ).sort((a, b) => a - b);

  const [form, setForm] = useState<SelectionForm>({
    subject_code: "",
    academic_year: "",
    semester_number: "",
  });
  const [saving, setSaving] = useState(false);
  const [requestForm, setRequestForm] = useState({
    subject_code: "",
    subject_name: "",
    semester_number: "",
  });
  const [requestSaving, setRequestSaving] = useState(false);
  const [editing, setEditing] = useState<FacultySelection | null>(null);
  const [editForm, setEditForm] = useState<SelectionForm>({
    subject_code: "",
    academic_year: "",
    semester_number: "",
  });
  const [editSaving, setEditSaving] = useState(false);

  useEffect(() => {
    if (!form.academic_year && years.data?.length) {
      const preferred =
        years.data.find((year) => year.academic_year === "2026-27") ?? years.data[0];
      setForm((current) => ({ ...current, academic_year: preferred.academic_year }));
    }
  }, [form.academic_year, years.data]);

  const chooseSubject = (code: string, current: SelectionForm, update: (next: SelectionForm) => void) => {
    update({
      ...current,
      subject_code: code,
      semester_number: subjectSemester(subjects.data ?? [], code) || current.semester_number,
    });
  };

  const saveSelection = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.subject_code || !form.academic_year || !form.semester_number) {
      notify("Choose a subject, academic year and semester.", "error");
      return;
    }
    setSaving(true);
    try {
      const result = await api<{ message: string }>("/faculty/me/selections", {
        method: "POST",
        body: {
          subject_code: form.subject_code,
          academic_year: form.academic_year,
          semester_number: Number(form.semester_number),
        },
      });
      notify(result.message, "success");
      setForm((current) => ({ ...current, subject_code: "", semester_number: "" }));
      selections.reload();
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The subject could not be selected.", "error");
    } finally {
      setSaving(false);
    }
  };

  const openEdit = (selection: FacultySelection) => {
    setEditing(selection);
    setEditForm({
      subject_code: selection.subject_code,
      academic_year: selection.academic_year,
      semester_number: String(selection.semester_number),
    });
  };

  const saveEdit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editing) return;
    setEditSaving(true);
    try {
      await api(`/faculty/me/selections/${editing.selection_id}`, {
        method: "PUT",
        body: {
          subject_code: editForm.subject_code,
          academic_year: editForm.academic_year,
          semester_number: Number(editForm.semester_number),
        },
      });
      notify("Subject selection updated.", "success");
      setEditing(null);
      selections.reload();
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The selection could not be updated.", "error");
    } finally {
      setEditSaving(false);
    }
  };

  const removeSelection = async (selection: FacultySelection) => {
    if (
      !window.confirm(
        `Remove ${selection.subject_code} for ${selection.academic_year}, semester ${selection.semester_number}? Existing feedback is preserved.`,
      )
    ) {
      return;
    }
    try {
      const result = await api<{ message: string }>(`/faculty/me/selections/${selection.selection_id}`, {
        method: "DELETE",
      });
      notify(result.message, "success");
      selections.reload();
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The selection could not be removed.", "error");
    }
  };

  const submitRequest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!requestForm.subject_code || !requestForm.subject_name || !requestForm.semester_number) {
      notify("Enter the subject code, name and semester.", "error");
      return;
    }
    setRequestSaving(true);
    try {
      const result = await api<{ message: string }>("/faculty/me/subject-requests", {
        method: "POST",
        body: {
          subject_code: requestForm.subject_code,
          subject_name: requestForm.subject_name,
          semester_number: Number(requestForm.semester_number),
        },
      });
      notify(result.message, "success");
      setRequestForm({ subject_code: "", subject_name: "", semester_number: "" });
      requests.reload();
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "The subject request could not be submitted.", "error");
    } finally {
      setRequestSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="My subjects"
        description="Choose the CSE subjects you teach. Your selections decide which offerings students can evaluate."
        actions={
          <Link to="/faculty">
            <Button variant="outline" icon={<ArrowLeft className="h-4 w-4" />}>
              Teaching overview
            </Button>
          </Link>
        }
      />

      <Alert variant="info">
        Administrators manage the official catalog, not faculty assignments. Every selection below is tied to your
        authenticated faculty account.
      </Alert>

      {[subjects, years, semesters, selections, requests].map((resource) =>
        resource.error ? <Alert variant="error" key={resource.error}>{resource.error}</Alert> : null,
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Select a subject</CardTitle>
            <p className="text-sm text-slate-500">You can select one or many subjects for any academic year and semester.</p>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={saveSelection}>
              <Field label="Subject" htmlFor="selection-subject">
                <Select
                  id="selection-subject"
                  value={form.subject_code}
                  required
                  onChange={(event) => chooseSubject(event.target.value, form, setForm)}
                >
                  <option value="">Select a CSE subject</option>
                  {(subjects.data ?? []).map((subject) => (
                    <option key={subject.subject_code} value={subject.subject_code}>
                      {subject.subject_code} · {subject.subject_name} (Sem {subject.semester_number})
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Academic year" htmlFor="selection-year">
                  <Select
                    id="selection-year"
                    value={form.academic_year}
                    required
                    onChange={(event) => setForm({ ...form, academic_year: event.target.value })}
                  >
                    <option value="">Select year</option>
                    {yearOptions.map((year) => (
                      <option key={year.academic_year} value={year.academic_year}>
                        {year.academic_year}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Semester" htmlFor="selection-semester">
                  <Select
                    id="selection-semester"
                    value={form.semester_number}
                    required
                    onChange={(event) => setForm({ ...form, semester_number: event.target.value })}
                  >
                    <option value="">Select semester</option>
                    {semesterOptions.map((semester) => (
                      <option key={semester} value={semester}>
                        Semester {semester}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <p className="text-xs text-slate-500">
                The semester is set from the catalog subject. A selection is stored for your account only.
              </p>
              <Button type="submit" loading={saving} icon={<Plus className="h-4 w-4" />}>
                Save selection
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Request a missing subject</CardTitle>
            <p className="text-sm text-slate-500">
              If your subject is not in the catalog, request it. An administrator must approve it before it becomes
              available.
            </p>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={submitRequest}>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Subject code" htmlFor="request-code">
                  <Input
                    id="request-code"
                    value={requestForm.subject_code}
                    required
                    minLength={2}
                    maxLength={20}
                    onChange={(event) => setRequestForm({ ...requestForm, subject_code: event.target.value.toUpperCase() })}
                  />
                </Field>
                <Field label="Semester" htmlFor="request-semester">
                  <Select
                    id="request-semester"
                    value={requestForm.semester_number}
                    required
                    onChange={(event) => setRequestForm({ ...requestForm, semester_number: event.target.value })}
                  >
                    <option value="">Select semester</option>
                    {semesterOptions.map((semester) => (
                      <option key={semester} value={semester}>
                        Semester {semester}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <Field label="Subject name" htmlFor="request-name">
                <Input
                  id="request-name"
                  value={requestForm.subject_name}
                  required
                  minLength={3}
                  maxLength={180}
                  onChange={(event) => setRequestForm({ ...requestForm, subject_name: event.target.value })}
                />
              </Field>
              <Button type="submit" loading={requestSaving} icon={<Send className="h-4 w-4" />}>
                Submit request
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>My selections</CardTitle>
          <p className="text-sm text-slate-500">Update the year or semester, or remove a selection you no longer teach.</p>
        </CardHeader>
        <CardContent>
          {selections.loading ? (
            <LoadingBlock label="Loading your subjects…" />
          ) : selections.data?.length ? (
            <Table>
              <thead>
                <tr>
                  <Th>Subject</Th>
                  <Th>Academic year</Th>
                  <Th>Semester</Th>
                  <Th>Feedback</Th>
                  <Th className="text-right">Actions</Th>
                </tr>
              </thead>
              <tbody>
                {selections.data.map((selection) => (
                  <tr key={selection.selection_id}>
                    <Td>
                      <p className="font-medium text-slate-900">{selection.subject_code}</p>
                      <p className="text-xs text-slate-500">{selection.subject_name}</p>
                    </Td>
                    <Td>{selection.academic_year}</Td>
                    <Td>{selection.semester_number}</Td>
                    <Td>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={selection.period_open ? "success" : "outline"}>
                          {selection.period_open ? "Open" : "Closed"}
                        </Badge>
                        <span className="text-xs text-slate-500">{selection.response_count} responses</span>
                      </div>
                    </Td>
                    <Td className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button size="sm" variant="outline" onClick={() => openEdit(selection)} icon={<Pencil className="h-3.5 w-3.5" />}>
                          Edit
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => void removeSelection(selection)} icon={<Trash2 className="h-3.5 w-3.5" />}>
                          Remove
                        </Button>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState
              title="No subjects selected"
              description="Select a subject above so students can evaluate it for the matching academic year and semester."
              icon={<BookOpen className="h-6 w-6" />}
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>My subject requests</CardTitle>
          <p className="text-sm text-slate-500">Requests are reviewed by an administrator before they enter the catalog.</p>
        </CardHeader>
        <CardContent>
          {requests.loading ? (
            <LoadingBlock label="Loading your requests…" />
          ) : requests.data?.length ? (
            <Table>
              <thead>
                <tr>
                  <Th>Subject</Th>
                  <Th>Semester</Th>
                  <Th>Status</Th>
                  <Th>Administrator note</Th>
                  <Th>Requested</Th>
                </tr>
              </thead>
              <tbody>
                {requests.data.map((item) => (
                  <tr key={item.request_id}>
                    <Td>
                      <p className="font-medium text-slate-900">{item.subject_code}</p>
                      <p className="text-xs text-slate-500">{item.subject_name}</p>
                    </Td>
                    <Td>{item.semester_number}</Td>
                    <Td>
                      <Badge
                        variant={
                          item.status === "approved" ? "success" : item.status === "rejected" ? "warning" : "default"
                        }
                      >
                        {item.status}
                      </Badge>
                    </Td>
                    <Td className="max-w-[240px] whitespace-normal text-xs text-slate-500">
                      {item.admin_note || "—"}
                    </Td>
                    <Td className="text-xs text-slate-500">{new Date(item.created_at).toLocaleDateString()}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState title="No subject requests" description="Request a missing subject and it will appear here." />
          )}
        </CardContent>
      </Card>

      <Modal
        open={Boolean(editing)}
        title="Edit subject selection"
        description="Changing the year or semester moves this offering. Selections with feedback cannot be moved."
        onClose={() => setEditing(null)}
      >
        <form className="space-y-4" onSubmit={saveEdit}>
          <Field label="Subject" htmlFor="edit-selection-subject">
            <Select
              id="edit-selection-subject"
              value={editForm.subject_code}
              required
              onChange={(event) => chooseSubject(event.target.value, editForm, setEditForm)}
            >
              <option value="">Select a CSE subject</option>
              {(subjects.data ?? []).map((subject) => (
                <option key={subject.subject_code} value={subject.subject_code}>
                  {subject.subject_code} · {subject.subject_name} (Sem {subject.semester_number})
                </option>
              ))}
            </Select>
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Academic year" htmlFor="edit-selection-year">
              <Select
                id="edit-selection-year"
                value={editForm.academic_year}
                required
                onChange={(event) => setEditForm({ ...editForm, academic_year: event.target.value })}
              >
                <option value="">Select year</option>
                {yearOptions.map((year) => (
                  <option key={year.academic_year} value={year.academic_year}>
                    {year.academic_year}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Semester" htmlFor="edit-selection-semester">
              <Select
                id="edit-selection-semester"
                value={editForm.semester_number}
                required
                onChange={(event) => setEditForm({ ...editForm, semester_number: event.target.value })}
              >
                <option value="">Select semester</option>
                {semesterOptions.map((semester) => (
                  <option key={semester} value={semester}>
                    Semester {semester}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button type="submit" loading={editSaving}>
              Save changes
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
