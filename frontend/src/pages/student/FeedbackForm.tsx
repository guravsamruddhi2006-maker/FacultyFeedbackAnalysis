import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Lock, ShieldCheck } from "lucide-react";

import {
  Alert,
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Field,
  LoadingBlock,
  PageHeader,
  Textarea,
} from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { useToast } from "@/context/ToastContext";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const ratingLabels = ["Very poor", "Poor", "Average", "Good", "Excellent"];

interface FormResponse {
  offering: {
    offering_id: number;
    academic_year: string;
    semester_number: number;
    subject_code: string;
    subject_name: string;
    faculty_name: string;
    start_date?: string | null;
    end_date?: string | null;
    period_open: boolean;
  };
  questions: Array<{ question_id: number; question_text: string }>;
  existing_feedback: null | {
    feedback_id: number;
    comment: string;
    submitted_at: string;
    updated_at?: string | null;
    editable: boolean;
    answers: Array<{ question_id: number; question_text: string; rating: number }>;
  };
  editable: boolean;
}

export function FeedbackFormPage() {
  const { offeringId } = useParams();
  const navigate = useNavigate();
  const { notify } = useToast();
  const { data, loading, error } = useApi<FormResponse>(
    offeringId ? `/students/me/feedback/${offeringId}` : null,
  );
  const [ratings, setRatings] = useState<Record<number, number>>({});
  const [comment, setComment] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!data) return;
    const next: Record<number, number> = {};
    data.existing_feedback?.answers.forEach((answer) => {
      next[answer.question_id] = answer.rating;
    });
    setRatings(next);
    setComment(data.existing_feedback?.comment ?? "");
  }, [data]);

  const editable = Boolean(data?.editable);
  const existing = data?.existing_feedback ?? null;
  const completed = useMemo(
    () => data?.questions.every((question) => ratings[question.question_id]) ?? false,
    [data, ratings],
  );

  const submit = async () => {
    setFormError(null);
    if (!completed) {
      setFormError("Please rate every statement before submitting.");
      return;
    }
    const trimmed = comment.trim();
    if (trimmed.length < 10) {
      setFormError("Please write at least 10 characters in your comment.");
      return;
    }
    if (trimmed.length > 1000) {
      setFormError("Comments cannot exceed 1000 characters.");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ratings: Object.entries(ratings).map(([questionId, rating]) => ({
          question_id: Number(questionId),
          rating,
        })),
        comment: trimmed,
      };
      if (existing) {
        await api(`/students/me/feedback/${existing.feedback_id}`, { method: "PUT", body: payload });
        notify("Feedback updated successfully.", "success");
      } else {
        await api("/students/me/feedback", {
          method: "POST",
          body: { offering_id: Number(offeringId), ...payload },
        });
        notify("Feedback submitted. Thank you for helping improve teaching.", "success");
      }
      navigate("/student");
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Could not save your feedback.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingBlock />;
  if (error || !data) {
    return (
      <div className="space-y-4">
        <Alert variant="error">{error ?? "This offering could not be loaded."}</Alert>
        <Link to="/student">
          <Button variant="outline" icon={<ArrowLeft className="h-4 w-4" />}>
            Back to dashboard
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between gap-3">
        <Link to="/student">
          <Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>
            Back
          </Button>
        </Link>
        <Badge variant={editable ? "success" : "outline"}>
          {editable ? "Editable" : "Read only"}
        </Badge>
      </div>

      <PageHeader
        title={`${data.offering.subject_code} · ${data.offering.subject_name}`}
        description={`Feedback for ${data.offering.faculty_name} · ${data.offering.academic_year}, semester ${data.offering.semester_number}`}
      />

      <Alert variant="info" title="Anonymous by design">
        <span className="flex items-start gap-2">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            Your name and USN are never shown to faculty. Only your ratings and comment text are analysed. The database
            keeps a one-way link solely to prevent duplicate submissions.
          </span>
        </span>
      </Alert>

      {!editable ? (
        <Alert variant="warning" title="This feedback window is closed">
          You can read your submitted response but cannot change it.{" "}
          {data.offering.end_date ? `The window closed on ${formatDate(data.offering.end_date)}.` : ""}
        </Alert>
      ) : null}

      {!editable && !existing ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <Lock className="h-8 w-8 text-slate-400" />
            <p className="font-medium text-slate-800">Feedback is not available</p>
            <p className="max-w-md text-sm text-slate-500">
              The feedback period for this offering has closed and no submission exists.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Rate each statement</CardTitle>
              <p className="text-sm text-slate-500">1 = very poor, 5 = excellent. Every statement is required.</p>
            </CardHeader>
            <CardContent className="divide-y">
              {data.questions.map((question, index) => (
                <div key={question.question_id} className="py-4 first:pt-0 last:pb-0">
                  <p className="text-sm font-medium text-slate-800">
                    {index + 1}. {question.question_text}
                  </p>
                  <div className="mt-2.5 grid grid-cols-5 gap-2">
                    {ratingLabels.map((label, position) => {
                      const value = position + 1;
                      const active = ratings[question.question_id] === value;
                      return (
                        <button
                          key={value}
                          type="button"
                          disabled={!editable}
                          onClick={() =>
                            setRatings((current) => ({ ...current, [question.question_id]: value }))
                          }
                          aria-pressed={active}
                          className={`rounded-md border px-1 py-2 text-xs font-medium transition ${
                            active
                              ? "border-primary bg-primary text-white shadow-sm"
                              : "border-input bg-white text-slate-600 hover:border-primary/50 hover:bg-blue-50 disabled:hover:border-input disabled:hover:bg-white"
                          } disabled:cursor-not-allowed disabled:opacity-70`}
                        >
                          <span className="block text-base font-semibold">{value}</span>
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Your comment</CardTitle>
              <p className="text-sm text-slate-500">
                Be specific and constructive. Between 10 and 1000 characters.
              </p>
            </CardHeader>
            <CardContent>
              <Field
                label="What worked well, and what could be improved?"
                htmlFor="comment"
                hint={`${comment.trim().length}/1000 characters`}
              >
                <Textarea
                  id="comment"
                  rows={6}
                  maxLength={1000}
                  disabled={!editable}
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="Example: The lectures were clear and the examples helped me understand the topic. More revision sessions before exams would help."
                />
              </Field>
            </CardContent>
          </Card>

          {formError ? <Alert variant="error">{formError}</Alert> : null}

          {editable ? (
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Link to="/student">
                <Button variant="outline" className="w-full sm:w-auto">
                  Cancel
                </Button>
              </Link>
              <Button loading={saving} onClick={submit} className="w-full sm:w-auto">
                {existing ? "Save changes" : "Submit anonymous feedback"}
              </Button>
            </div>
          ) : existing ? (
            <Alert variant="success" title="Your submission">
              Submitted on {formatDate(existing.submitted_at)}.
            </Alert>
          ) : null}
        </>
      )}
    </div>
  );
}
