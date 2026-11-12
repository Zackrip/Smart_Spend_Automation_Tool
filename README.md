# Smart Spend

> Intelligent personal expense management and budget automation platform.

Smart Spend helps you track spending, understand where your money goes, and optimize your budget with minimal manual effort. A **MERN** web app handles the user experience, while a **Python automation bot** handles parsing, categorization, forecasting and alerts.

![Status](https://img.shields.io/badge/status-in%20development-orange)
![Stack](https://img.shields.io/badge/stack-MERN%20%2B%20Python-blue)
![Phase](https://img.shields.io/badge/phase-1%20MVP-green)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Overview](#api-overview)
- [Roadmap and Progress](#roadmap-and-progress)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Features

**Core (MVP)**
- User registration, login and JWT-based sessions
- Income and expense tracking (add, edit, delete, filter, search)
- Default and custom categories
- Monthly budgets per category
- Dashboard with spending summary and charts
- CSV export

**Automation (Python bot)**
- Bank statement import (CSV, Excel, PDF)
- SMS and email alert parsing (UPI and card formats)
- Rule-based, then ML-based, auto-categorization
- Duplicate and recurring-payment detection
- Budget threshold alerts and scheduled reports

**Intelligence (planned)**
- Month-end spend forecasting
- Anomaly and unusual-charge detection
- Budget optimization suggestions
- Savings goals and a financial health score
- Receipt OCR and a natural language assistant

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Backend | Node.js, Express.js, Pg |
| Database | Postgres (PgSQL) |
| Validation | Zod |
| Auth | JWT, bcrypt |
| Cache and Queue | Redis, BullMQ (planned) |
| Automation Bot | Python 3.11+, FastAPI, pandas, scikit-learn (planned) |
| DevOps | Docker, GitHub Actions (planned) |

---

## Architecture

```
React Frontend  <--REST/JWT-->  Node/Express API  <-->  Postgres
                                      |
                                 Redis / BullMQ
                                      |
                             Python Automation Bot
                      (parsers, categorizer, forecaster, alerts)
```

- The **Node API** owns business logic and user data.
- The **Python bot** owns automation and ML, and works through a job queue so heavy tasks never block users.

---

## Project Structure

Adjust to match your repository layout.

```
smart-spend/
  client/                    # React frontend
  server/                    # Node/Express backend
    controllers/
    models/
    routes/
    middleware/
    validators/
    seeds/
    app.js
  bot/                       # Python automation bot (planned)
  docs/                      # Documentation
  README.md
```

---

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Postgres (local or PgAdmin connection string)
- Python 3.11+ (only needed for the bot, later phases)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd smart-spend

# 2. Install backend dependencies
cd server
npm install

# 3. Install frontend dependencies
cd ../client
npm install
```

### Configure environment

Create a `.env` file inside `server/` (see [Environment Variables](#environment-variables)).

### Seed default data

```bash
cd server
node seeds/seedCategories.js
```

### Run the app

```bash
# Backend (from /server)
npm run dev

# Frontend (from /client)
npm run dev
```

Backend runs on `http://localhost:5000` and the frontend on `http://localhost:5173` by default.

---

## Environment Variables

**server/.env**

```env
PORT=5000

JWT_SECRET=replace_with_a_long_random_string
JWT_EXPIRES_IN=15m
CLIENT_URL=http://localhost:5173
```

Never commit `.env` files. Make sure `.env` is listed in `.gitignore`.

---

## API Overview

Base URL: `/api/v1`. All endpoints except auth require `Authorization: Bearer <token>`.

| Module | Endpoint | Status |
|---|---|---|
| Auth | `POST /auth/register`, `POST /auth/login` | Done |
| Categories | `GET/POST /categories`, `PUT/DELETE /categories/:id` | Done |
| Transactions | `GET/POST /transactions`, `GET/PUT/DELETE /transactions/:id` | Next |
| Budgets | `GET/POST/PUT/DELETE /budgets` | Planned |
| Analytics | `GET /analytics/summary`, `/trends`, `/category-breakdown` | Planned |
| Imports | `POST /imports` | Planned |
| Goals and Insights | `GET/POST /goals`, `GET /insights` | Planned |

Example request:

```bash
curl -X POST http://localhost:5000/api/v1/categories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Gym","type":"expense","color":"#22c55e"}'
```

Validation errors return a `400` with per-field messages:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [{ "field": "name", "message": "..." }]
}
```

---

## Roadmap and Progress

| Phase | Scope | Status |
|---|---|---|
| 0. Discovery and Setup | Requirements, design, environment | Done |
| 1. MVP (MERN core) | Auth, categories, transactions, budgets, dashboard | In progress |
| 2. Automation (Bot v1) | Statement import, parsers, rule-based categorization, alerts | Planned |
| 3. Intelligence (Bot v2) | ML categorization, forecasting, anomalies, insights | Planned |
| 4. Hardening and Launch | Security audit, performance, beta | Planned |
| 5. Growth and Scale | Mobile app, bank integrations, premium features | Planned |

**Phase 1 checklist**

- [x] Authentication
- [x] Categories
- [ ] Transactions (backend and UI)
- [ ] Budgets
- [ ] Dashboard and charts
- [ ] CSV export
- [ ] Tests and staging deployment

---

## Testing

```bash
# Backend
cd server
npm test
```

Planned tooling: Jest and Supertest (API), React Testing Library (UI), pytest (bot), Playwright or Cypress (end to end).

---

## Security

- Passwords are hashed and never returned in API responses.
- Every query is scoped to the authenticated user.
- Request bodies are validated with Zod, and unknown fields are stripped.
- Secrets live in environment variables, never in Git.
- Planned: rate limiting, Helmet, CORS allowlist, encryption of sensitive fields.

To report a vulnerability, please contact the maintainer privately instead of opening a public issue.

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feature/your-feature`
2. Commit with clear messages: `git commit -m "feat: add transaction filters"`
3. Push the branch and open a Pull Request

Please keep pull requests focused and include tests where possible.

---

## License

Distributed under the MIT License. See `LICENSE` for details.

---

*Built with the MERN stack and Python.*
