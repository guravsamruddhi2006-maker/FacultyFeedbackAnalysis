# 03 — Technology Stack

> **FacultyInsight AI** · Documentation set · [Back to index](../README.md#documentation-index)

All versions below are pinned in `backend/requirements.txt` and `frontend/package.json` unless marked with a caret range. Use these exact versions when reproducing the environment.

## 3.1 Backend

| Package | Version | Role |
|---------|---------|------|
| Python | 3.12 (Docker `python:3.12-slim`) | Runtime |
| `fastapi` | 0.143.0 | Web framework, routing, validation, OpenAPI |
| `starlette` | 1.6.0 | ASGI toolkit under FastAPI |
| `uvicorn[standard]` | 0.54.0 | ASGI server |
| `psycopg[binary]` | 3.3.6 | PostgreSQL driver (v3) |
| `bcrypt` | 5.0.0 | Password hashing |
| `PyJWT` | 2.15.1 | JWT encode/decode |
| `python-dotenv` | 1.2.4 | `.env` loading |
| `pydantic` | 2.14.1 | Request/response models |
| `scikit-learn` | 1.9.1 | Optional TF-IDF model training/serving |
| `pandas` | 3.0.6 | Data handling for the ML training script |
| `numpy` | 2.5.4 | Numeric dependency |
| `matplotlib` | 3.11.2 | Figure generation for ML/report tooling |
| `reportlab` | 5.1.0 | PDF report generation |
| `joblib` | 1.6.0 | Model serialisation |
| `httpx` | 0.28.1 | HTTP client (tests) |
| `pytest` | 9.2.0 | Test runner |

Install everything with:

```powershell
pip install -r backend/requirements.txt
```

## 3.2 Frontend

| Package | Version | Role |
|---------|---------|------|
| Node.js | 20 (Docker `node:20-alpine`) | Build/runtime toolchain |
| `react` | ^18.3.1 | UI library |
| `react-dom` | ^18.3.1 | DOM renderer |
| `react-router-dom` | ^6.28.1 | Client-side routing |
| `typescript` | ^5.9.3 | Type checking |
| `vite` | ^6.0.7 | Dev server and bundler |
| `@vitejs/plugin-react` | ^4.3.4 | React support for Vite |
| `tailwindcss` | ^3.4.17 | Utility CSS |
| `postcss` | ^8.4.49 | CSS pipeline |
| `autoprefixer` | ^10.4.20 | Vendor prefixes |
| `recharts` | ^2.15.0 | Charts |
| `lucide-react` | ^0.468.0 | Icons |
| `react-hook-form` | ^7.54.2 | Forms |
| `@hookform/resolvers` | ^3.9.1 | Zod resolver |
| `zod` | ^3.24.1 | Client-side validation |
| `clsx` | ^2.1.1 | Conditional class names |
| `tailwind-merge` | ^2.6.0 | Class de-duplication |
| `class-variance-authority` | ^0.7.1 | Variant styling |
| `vitest` | ^5.1.0 | Unit test runner |
| `@testing-library/react` | ^16.3.3 | Component testing |
| `@testing-library/jest-dom` | ^7.0.1 | DOM matchers |
| `@testing-library/user-event` | ^14.6.12 | User interaction simulation |
| `jsdom` | ^31.0.1 | DOM environment |
| `@playwright/test` | ^1.65.1 | End-to-end test runner (optional) |

Install with:

```powershell
cd frontend
npm ci
```

> `npm ci` installs exactly what `package-lock.json` records. Use `npm install` only when intentionally changing dependencies.

## 3.3 Database

| Item | Value |
|------|-------|
| Engine | PostgreSQL 18 |
| Production host | Neon (managed, serverless Postgres) |
| Local host | `localhost:5432` (native install or Docker) |
| Driver | `psycopg` 3.3.6 |
| Row factory | `dict_row` for readable mappings |

## 3.4 Hosting and tooling

| Item | Value |
|------|-------|
| Source control | Git, hosted on GitHub |
| Production hosting | Vercel (static frontend + Python serverless function) |
| Local containers | Docker + Docker Compose (Postgres, Uvicorn, Nginx) |
| Reverse proxy in containers | Nginx 1.27 Alpine |
| CI | None configured as a pipeline; tests are run manually |

## 3.5 Version policy notes

- Backend dependencies are **pinned exactly** (`==`) for reproducible deploys.
- Frontend dependencies use caret ranges but are locked by `package-lock.json`.
- The production environment is whatever Vercel installs from these manifests; the versions above are the ones present in the repository lockfiles at the time of writing.
- Python 3.12 is the supported runtime. The Docker image and local `.venv` should match to avoid driver or wheel differences.

## 3.6 Why these choices

| Choice | Reason |
|--------|--------|
| FastAPI | Typed request models, automatic validation, good performance, simple dependency injection |
| psycopg 3 | Modern PostgreSQL driver with native parameter binding |
| React + Vite | Fast builds, small bundles, familiar component model |
| Tailwind | Consistent styling without a large component library |
| Recharts | Declarative charts that fit the analytics screens |
| ReportLab | Pure-Python PDF generation, no external binary |
| Neon | Managed Postgres with a free tier and branching |
| Vercel | One deploy for the SPA and the Python function |

## 3.7 Related documents

- [04 — Project Structure](./04-project-structure.md)
- [16 — Installation on Windows](./16-installation-on-windows.md)
- [17 — Deployment](./17-deployment.md)

---

**Next:** [04 — Project Structure →](./04-project-structure.md)
