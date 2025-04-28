# 🚚 Real-Time Delivery Control System

A lightweight web application that monitors and manages Korean delivery orders **in real time**.  


---

## 🏗️ Architecture & Technology Stack

| Layer        | Technology                                           | Notes |
|--------------|------------------------------------------------------|-------|
| **Backend**  | **Python 3.12.9**, FastAPI, Jinja2 (SSR)             | Single-container application :contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3} |
| **Frontend** | HTML + CSS, modular JavaScript                       | Namespaced to avoid global collisions |
| **Database** | **MySQL 8.0** (schema from `init-db.sql`)            | Cloud SQL with Private IP & IAM DB Auth |
| **Infra**    | Docker (single container) → **GAE Flexible Env.**    | `runtime: custom`; static assets via FastAPI `StaticFiles` |
| **Locale**   | UTF-8, **KST (UTC+9)**                               | All date-time fields use `YYYY-MM-DD HH:MM` |

> **Design principles** — Simplicity, YAGNI, SSR-first, explicit user actions, and front-end validation priority. :contentReference[oaicite:4]{index=4}&#8203;:contentReference[oaicite:5]{index=5}

---

## 🔐 Security Configuration

| Area          | Measures |
|---------------|----------|
| **GAE Flex**  | Cloud Armor DDoS/TLS, firewall allow-list, `Strict-Transport-Security`, `X-Content-Type-Options`, and `X-Frame-Options` headers :contentReference[oaicite:6]{index=6}&#8203;:contentReference[oaicite:7]{index=7} |
| **Cloud SQL** | Private IP, SSL connections, IAM DB Auth, automated backups, least-privilege parameters |
| **Sessions**  | Server-side sessions, `httponly` + `secure` cookies, automatic logout on expiry |
| **Input Validation** | Critical integrity checks on the server; all other validation on the client |
| **Logging & API Responses** | Minimal PII, unified JSON response format `{success, error_code, message}` |

---

## 🚀 Deployment

### 1 · Local Docker Setup
```bash
git clone https://github.com/your-org/realtime-delivery.git
cd realtime-delivery

# Copy and edit environment variables
cp .env.example .env

# Build & run
docker build -t realtime-delivery .
docker run -p 8080:8080 --env-file .env realtime-delivery
