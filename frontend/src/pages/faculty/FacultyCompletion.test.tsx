import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { ToastProvider } from "@/context/ToastContext";
import { FacultyCompletionPage } from "@/pages/faculty/FacultyCompletion";
import type { CompletionSummary, FacultySelection } from "@/lib/types";

const SELECTION: FacultySelection = {
  selection_id: 1,
  faculty_id: 7,
  subject_code: "CS501",
  subject_name: "Data Structures",
  academic_year: "2026-27",
  semester_number: 5,
  is_active: true,
  offering_id: 3,
  response_count: 1,
  period_open: true,
};

function completion(overrides: Partial<CompletionSummary> = {}): CompletionSummary {
  return {
    subject_code: "CS501",
    subject_name: "Data Structures",
    academic_year: "2026-27",
    semester_number: 5,
    period: { start_date: "2026-11-01", end_date: "2026-11-30", is_open: true },
    roster_available: true,
    eligible_count: 2,
    submitted_count: 1,
    pending_count: 1,
    completion_percentage: 50,
    pending_students: [{ student_id: "4UB26CS002", name: "Beta Student" }],
    privacy_notice:
      "Completion tracking shows only whether a student submitted. Faculty never see who submitted which rating or comment.",
    methodology:
      "Counts use the verified class roster for this subject, year and semester.",
    ...overrides,
  };
}

function stubApi(summary: CompletionSummary) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      const body = url.includes("/faculty/me/completion") ? summary : [SELECTION];
      return Promise.resolve(
        new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <FacultyCompletionPage />
      </ToastProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("FacultyCompletionPage", () => {
  it("shows completion counts and only the pending students", async () => {
    stubApi(completion());
    renderPage();

    expect(await screen.findByText("Pending students")).toBeInTheDocument();
    expect(await screen.findByText("Beta Student")).toBeInTheDocument();
    expect(screen.getByText("4UB26CS002")).toBeInTheDocument();
    expect(screen.getByText("50.0%")).toBeInTheDocument();
    expect(screen.getByText("1 / 2 (50.0%)")).toBeInTheDocument();

    // The submitted student and feedback content must never appear.
    expect(screen.queryByText("4UB26CS001")).not.toBeInTheDocument();
    expect(screen.queryByText(/The private comment/)).not.toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /Download pending PDF/i }),
    ).toBeEnabled();
    expect(
      screen.getByRole("button", { name: /Share reminder on WhatsApp/i }),
    ).toBeEnabled();
  });

  it("disables exports and explains when no verified roster exists", async () => {
    stubApi(
      completion({
        roster_available: false,
        eligible_count: 0,
        submitted_count: 0,
        pending_count: 0,
        completion_percentage: 0,
        pending_students: [],
      }),
    );
    renderPage();

    expect(
      await screen.findByText("Verified class roster not available"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Download pending PDF/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Share reminder on WhatsApp/i }),
    ).not.toBeInTheDocument();
  });
});
