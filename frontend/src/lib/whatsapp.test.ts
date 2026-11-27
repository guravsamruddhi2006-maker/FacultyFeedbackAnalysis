import { describe, expect, it } from "vitest";

import { buildReminderMessage, whatsappShareUrl } from "@/lib/whatsapp";

const INPUT = {
  subjectCode: "CS501",
  subjectName: "Data Structures",
  academicYear: "2026-27",
  semesterNumber: 5,
  eligibleCount: 40,
  submittedCount: 27,
  pendingCount: 13,
  completionPercentage: 67.5,
};

describe("WhatsApp reminder", () => {
  it("states aggregate progress without any student identity", () => {
    const message = buildReminderMessage(INPUT);

    expect(message).toContain("CS501 — Data Structures");
    expect(message).toContain("Semester 5");
    expect(message).toContain("27 of 40 enrolled students have submitted (67.5%)");
    expect(message).toContain("13 students still pending");
    expect(message).toContain("faculty never see who submitted");
    // No USN, student name, phone number or feedback content may appear.
    expect(message).not.toMatch(/4UB\d/i);
    expect(message).not.toMatch(/\b\d{10}\b/);
    expect(message).not.toMatch(/rating:\s*\d|comment:\s|score\s*[:=]\s*\d/i);
    expect(message).not.toContain("Alpha Student");
  });

  it("congratulates a fully submitted class instead of inventing pending students", () => {
    const message = buildReminderMessage({
      ...INPUT,
      submittedCount: 40,
      pendingCount: 0,
      completionPercentage: 100,
    });

    expect(message).toContain("All enrolled students have submitted.");
    expect(message).toContain("100.0%");
  });

  it("builds a user-controlled wa.me share link with an encoded message", () => {
    const message = buildReminderMessage(INPUT);
    const url = whatsappShareUrl(message);

    expect(url.startsWith("https://wa.me/?text=")).toBe(true);
    expect(url).not.toContain("+");
    expect(decodeURIComponent(url.split("text=")[1])).toBe(message);
  });
});
