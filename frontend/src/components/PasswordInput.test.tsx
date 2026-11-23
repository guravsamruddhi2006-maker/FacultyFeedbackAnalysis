import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { FormEvent } from "react";

import { PasswordInput } from "@/components/ui";

describe("PasswordInput", () => {
  it("hides the value initially and toggles it without changing it", () => {
    render(<PasswordInput id="password" aria-label="Password" defaultValue="Secret1Pass" />);

    const input = screen.getByLabelText("Password") as HTMLInputElement;
    expect(input).toHaveAttribute("type", "password");
    expect(input.value).toBe("Secret1Pass");

    fireEvent.click(screen.getByRole("button", { name: "Show password" }));
    expect(input).toHaveAttribute("type", "text");
    expect(input.value).toBe("Secret1Pass");
    expect(screen.getByRole("button", { name: "Hide password" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Hide password" }));
    expect(input).toHaveAttribute("type", "password");
    expect(input.value).toBe("Secret1Pass");
  });

  it("toggles each password field independently", () => {
    render(
      <>
        <PasswordInput id="first" aria-label="First password" defaultValue="First1Pass" />
        <PasswordInput id="second" aria-label="Second password" defaultValue="Second1Pass" />
      </>,
    );

    const first = screen.getByLabelText("First password") as HTMLInputElement;
    const second = screen.getByLabelText("Second password") as HTMLInputElement;
    const [firstToggle, secondToggle] = screen.getAllByRole("button", { name: "Show password" });

    fireEvent.click(firstToggle);
    expect(first).toHaveAttribute("type", "text");
    expect(second).toHaveAttribute("type", "password");
    expect(first.value).toBe("First1Pass");
    expect(second.value).toBe("Second1Pass");

    fireEvent.click(secondToggle);
    expect(first).toHaveAttribute("type", "text");
    expect(second).toHaveAttribute("type", "text");
  });

  it("does not submit the surrounding form", () => {
    const onSubmit = vi.fn((event: FormEvent<HTMLFormElement>) => event.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <PasswordInput id="password" aria-label="Password" />
      </form>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Show password" }));
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
