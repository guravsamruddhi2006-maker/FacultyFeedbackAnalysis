export interface ReminderMessageInput {
  subjectCode: string;
  subjectName: string;
  academicYear: string;
  semesterNumber: number;
  eligibleCount: number;
  submittedCount: number;
  pendingCount: number;
  completionPercentage: number;
}

/**
 * Build a reminder that contains aggregate counts only.
 *
 * It deliberately never includes student names, USNs, phone numbers, ratings or
 * comments. The faculty member decides whether to share it, and attaches the PDF
 * manually if they want the pending list.
 */
export function buildReminderMessage(input: ReminderMessageInput): string {
  const percentage = input.completionPercentage.toFixed(1);
  const progress = `${input.submittedCount} of ${input.eligibleCount} enrolled students have submitted (${percentage}%).`;
  const remaining =
    input.pendingCount > 0
      ? `${input.pendingCount} student${input.pendingCount === 1 ? "" : "s"} still pending.`
      : "All enrolled students have submitted.";

  return [
    "Hello,",
    "",
    `This is a reminder about anonymous faculty feedback for ${input.subjectCode} — ${input.subjectName} (${input.academicYear}, Semester ${input.semesterNumber}).`,
    "",
    `Progress: ${progress}`,
    remaining,
    "",
    "Please submit before the feedback period closes. Responses are anonymous: faculty never see who submitted which rating or comment.",
    "",
    "Thank you.",
  ].join("\n");
}

export function whatsappShareUrl(message: string): string {
  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall through to the legacy path.
  }

  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const copied = document.execCommand("copy");
    area.remove();
    return copied;
  } catch {
    return false;
  }
}
