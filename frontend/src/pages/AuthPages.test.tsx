import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";

import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/context/ToastContext";
import { AdminSetupPage, LoginPage, RegisterPage } from "@/pages/AuthPages";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderPage(page: ReactNode) {
  return render(
    <AuthProvider>
      <ToastProvider>
        <MemoryRouter>{page}</MemoryRouter>
      </ToastProvider>
    </AuthProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("authentication pages", () => {
  it("does not show marketing copy on the sign-in page", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ completed: false })));
    renderPage(<LoginPage />);

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.queryByText(/Turning student feedback/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Better teaching, together/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Academic feedback platform/i)).not.toBeInTheDocument();
    await screen.findByText("Create the first admin");
  });

  it("hides the first-admin link once setup is complete", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ completed: true }));
    vi.stubGlobal("fetch", fetchMock);
    renderPage(<LoginPage />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(screen.queryByText("Create the first admin")).not.toBeInTheDocument();
  });

  it("replaces the setup form with a sign-in option when setup is complete", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ completed: true })));
    renderPage(<AdminSetupPage />);

    expect(await screen.findByRole("heading", { name: "Setup already completed" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Create administrator" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go to sign in" })).toBeInTheDocument();
  });

  it("shows the setup form only while setup is still required", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ completed: false })));
    renderPage(<AdminSetupPage />);

    expect(await screen.findByRole("button", { name: "Create administrator" })).toBeInTheDocument();
  });

  it("toggles the sign-in password without changing its value", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ completed: true })));
    renderPage(<LoginPage />);

    const password = screen.getByLabelText("Password") as HTMLInputElement;
    fireEvent.change(password, { target: { value: "Secret1Pass" } });
    expect(password).toHaveAttribute("type", "password");

    fireEvent.click(screen.getByRole("button", { name: "Show password" }));
    expect(password).toHaveAttribute("type", "text");
    expect(password.value).toBe("Secret1Pass");

    fireEvent.click(screen.getByRole("button", { name: "Hide password" }));
    expect(password).toHaveAttribute("type", "password");
    expect(password.value).toBe("Secret1Pass");
  });

  it("toggles registration password fields independently", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse([])));
    renderPage(<RegisterPage kind="student" />);

    const password = screen.getByLabelText("Password") as HTMLInputElement;
    const confirmPassword = screen.getByLabelText("Confirm password") as HTMLInputElement;
    fireEvent.change(password, { target: { value: "Secret1Pass" } });
    fireEvent.change(confirmPassword, { target: { value: "Secret1Pass" } });

    const [firstToggle] = screen.getAllByRole("button", { name: "Show password" });
    fireEvent.click(firstToggle);

    expect(password).toHaveAttribute("type", "text");
    expect(confirmPassword).toHaveAttribute("type", "password");
    expect(password.value).toBe("Secret1Pass");
    expect(confirmPassword.value).toBe("Secret1Pass");
  });

  it("toggles setup password fields independently", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ completed: false })));
    renderPage(<AdminSetupPage />);

    const password = await screen.findByLabelText("Password");
    const confirmPassword = screen.getByLabelText("Confirm password");
    fireEvent.change(password, { target: { value: "Secret1Pass" } });
    fireEvent.change(confirmPassword, { target: { value: "Secret1Pass" } });

    const [, secondToggle] = screen.getAllByRole("button", { name: "Show password" });
    fireEvent.click(secondToggle);

    expect(password).toHaveAttribute("type", "password");
    expect(confirmPassword).toHaveAttribute("type", "text");
    expect(password).toHaveValue("Secret1Pass");
    expect(confirmPassword).toHaveValue("Secret1Pass");
  });
});
