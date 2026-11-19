import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AboutPage, LandingPage } from "@/pages/Public";

describe("Public pages", () => {
  it("renders the landing page headline", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Turning student feedback into better teaching/i)).toBeInTheDocument();
  });

  it("renders the about page mission", () => {
    render(
      <MemoryRouter>
        <AboutPage />
      </MemoryRouter>,
    );
    expect(screen.getByText(/About FacultyInsight AI/i)).toBeInTheDocument();
  });
});
