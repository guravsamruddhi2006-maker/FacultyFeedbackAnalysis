export type Role = "admin" | "faculty" | "student";

export interface AuthUser {
  id: string;
  role: Role;
  name: string;
  email?: string | null;
  department_id?: number | null;
  status?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: AuthUser;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  faculty_count?: number;
  student_count?: number;
}

export interface Subject {
  subject_code: string;
  subject_name: string;
  semester_number: number;
}

export interface FacultySelection {
  selection_id: number;
  faculty_id: number;
  subject_code: string;
  subject_name: string;
  academic_year: string;
  semester_number: number;
  is_active: boolean;
  offering_id: number | null;
  response_count: number;
  period_open: boolean;
  created_at?: string;
  updated_at?: string | null;
}

export interface SubjectRequest {
  request_id: number;
  faculty_id: number;
  faculty_name?: string;
  faculty_email?: string;
  subject_code: string;
  subject_name: string;
  semester_number: number;
  status: "pending" | "approved" | "rejected";
  admin_note?: string | null;
  reviewed_by?: number | null;
  reviewed_by_name?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  in_catalog?: boolean;
}

export interface FacultyMember {
  faculty_id: number;
  name: string;
  email: string;
  department_id: number;
  department_name?: string;
  status: string;
  created_at?: string;
  offering_count?: number;
  response_count?: number;
}

export interface StudentRow {
  student_id: string;
  name: string;
  department_id: number;
  department_name?: string;
  created_at?: string;
  feedback_count?: number;
}

export interface Offering {
  offering_id: number;
  academic_year: string;
  semester_number: number;
  subject_code: string;
  subject_name: string;
  faculty_id: number;
  faculty_name: string;
  start_date?: string | null;
  end_date?: string | null;
  period_open?: boolean;
  feedback_id?: number | null;
  submitted_at?: string | null;
  status?: "submitted" | "pending" | "closed";
  response_count?: number;
}

export interface Question {
  question_id: number;
  question_text: string;
  is_active?: boolean;
}

export interface FeedbackPeriod {
  academic_year: string;
  semester_number: number;
  start_date: string;
  end_date: string;
  is_open: boolean;
}

export interface QuestionStat {
  question_id: number;
  question_text: string;
  average_rating: number;
  response_count: number;
}

export interface RatingBucket {
  rating: number;
  label: string;
  count: number;
  percentage: number;
}

export interface CommentRow {
  feedback_id: number;
  comment: string;
  submitted_at: string;
  academic_year: string;
  semester_number: number;
  subject_code: string;
  subject_name: string;
  sentiment: {
    label: "positive" | "neutral" | "negative";
    score: number;
    confidence: number;
    method: string;
    limitations: string;
    matched_terms: string[];
  };
}

export interface SentimentSummary {
  total_comments: number;
  positive: number;
  neutral: number;
  negative: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  method: string;
  limitations: string;
}

export interface Analytics {
  faculty_id?: number;
  overall: { average_rating: number; response_count: number };
  question_stats: QuestionStat[];
  rating_distribution: RatingBucket[];
  subject_summary: Array<{
    academic_year: string;
    semester_number: number;
    subject_code: string;
    subject_name: string;
    response_count: number;
    average_rating: number;
  }>;
  trend: Array<{ academic_year?: string; label?: string; average_rating: number; response_count: number }>;
  comments: CommentRow[];
  strengths: Array<{ title: string; evidence: string; average_rating: number; response_count: number }>;
  improvement_areas: Array<{ title: string; evidence: string; average_rating: number; response_count: number }>;
  sentiment: {
    summary: SentimentSummary;
    positive_comments: CommentRow[];
    negative_comments: CommentRow[];
    topics: Array<{ topic: string; mentions: number; positive: number; neutral: number; negative: number }>;
    keywords: Array<{ keyword: string; weight: number }>;
  };
  filter_options: FilterOptions;
  privacy_notice: string;
  insights?: {
    generated_at: string | null;
    overall_average_rating: number;
    response_count: number;
    strengths: Array<{
      area: string;
      average_rating: number;
      response_count: number;
      strength: boolean;
    }>;
    improvement_areas: Array<{
      area: string;
      average_rating: number;
      response_count: number;
      recommendation: string;
    }>;
    recommendations: Array<{
      area: string;
      average_rating: number;
      response_count: number;
      recommendation: string;
      rationale: string;
      evidence_level: string;
      threshold_met: boolean;
    }>;
    trend_insights: Array<Record<string, unknown>>;
    sentiment: SentimentSummary & { topics: Array<{ topic: string; mentions: number; positive: number; neutral: number; negative: number }> };
    methodology: {
      rating_averaging: string;
      strength_threshold: string;
      improvement_threshold: string;
      evidence_required: boolean;
    };
  };
}

export interface FilterOptions {
  academic_years: string[];
  semesters: number[];
  subjects: Array<{ subject_code: string; subject_name: string }>;
  faculty: Array<{ faculty_id: number; name: string }>;
}
