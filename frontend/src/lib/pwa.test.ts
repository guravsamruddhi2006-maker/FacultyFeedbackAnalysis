import { describe, expect, it } from "vitest";

import manifestRaw from "../../public/manifest.webmanifest?raw";
import swRaw from "../../public/sw.js?raw";
import offlineRaw from "../../public/offline.html?raw";
import indexHtml from "../../index.html?raw";
import icon192 from "../../public/icons/icon-192.png?url";
import icon512 from "../../public/icons/icon-512.png?url";
import iconMaskable from "../../public/icons/icon-maskable-512.png?url";
import appleTouchIcon from "../../public/icons/apple-touch-icon.png?url";

describe("PWA assets", () => {
  it("publishes an installable manifest with matching icons and standalone display", () => {
    const manifest = JSON.parse(manifestRaw);

    expect(manifest.name).toBe("FacultyInsight AI");
    expect(manifest.start_url).toBe("/");
    expect(manifest.scope).toBe("/");
    expect(manifest.display).toBe("standalone");
    expect(manifest.theme_color).toBe("#0b1f3a");
    expect(manifest.background_color).toBe("#0b1f3a");
    expect(Array.isArray(manifest.icons)).toBe(true);

    const sizes = manifest.icons.map((icon: { sizes: string }) => icon.sizes);
    expect(sizes).toContain("192x192");
    expect(sizes).toContain("512x512");
    expect(
      manifest.icons.some((icon: { purpose?: string }) => icon.purpose === "maskable"),
    ).toBe(true);

    // The bundler resolves each referenced file; a missing icon breaks the test.
    expect(icon192).toBeTruthy();
    expect(icon512).toBeTruthy();
    expect(iconMaskable).toBeTruthy();
    expect(appleTouchIcon).toBeTruthy();
  });

  it("never caches API responses in the service worker", () => {
    expect(swRaw).toContain('url.pathname.startsWith("/api/")');
    expect(swRaw).toContain("OFFLINE_URL");
    expect(swRaw).toContain("SKIP_WAITING");
    expect(swRaw).not.toMatch(/caches\.put\([^)]*api/i);
  });

  it("ships a branded offline fallback that never queues feedback", () => {
    expect(offlineRaw).toContain("FacultyInsight AI");
    expect(offlineRaw).toContain("You are offline");
    expect(offlineRaw.toLowerCase()).toContain("never queued");
    expect(offlineRaw).toContain("Try again");
  });

  it("links the manifest and touch icon from the app shell", () => {
    expect(indexHtml).toContain('rel="manifest" href="/manifest.webmanifest"');
    expect(indexHtml).toContain('rel="apple-touch-icon"');
    expect(indexHtml).toContain('name="theme-color" content="#0b1f3a"');
  });
});
