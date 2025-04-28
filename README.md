# 🚚 Real‑Time Delivery Control System

> **Work in progress** — This shared README is a **sample** and may differ from the deployed production version. Please use it for reference only.

A lightweight web application that monitors and manages **TWLKR CS** delivery orders in real time.

---

## 🏗️ Architecture & Technology Stack

**Backend**  
- Python 3.12  
- FastAPI  
- Jinja2 (SSR)

**Frontend**  
- HTML & CSS  
- Modular JavaScript (namespaced to avoid global collisions)

**Database**  
- MySQL 8.0 (schema defined in `init-db.sql`)  
- Cloud SQL (Private IP & IAM DB Auth)

**Infrastructure**  
- Docker container deployed to Google App Engine Flexible Environment (`runtime: custom`)  
- Static assets served via FastAPI `StaticFiles`

**Locale**  
- UTF‑8, KST (UTC+9)  
- All date‑time fields follow the `YYYY-MM-DD HH:MM` format

---

## 🔐 Security Configuration

**GAE Flex**  
- Cloud Armor (DDoS / TLS)  
- Firewall allow‑list  
- HTTP Strict Transport Security  
- `X-Content-Type-Options`, `X-Frame-Options`

**Cloud SQL**  
- Private IP  
- SSL/TLS connections  
- IAM‑based authentication  
- Automated backups  
- Least‑privilege parameter tuning

**Sessions**  
- Server‑side sessions  
- `HttpOnly` + `Secure` cookies  
- Automatic logout on expiry

**Input Validation**  
- Critical integrity checks on the server  
- Complementary validation on the client

**Logging & API Responses**  
- No persistent PII  
- Unified JSON response schema `{success, error_code, message}`

---

**Design principles** — Simplicity, YAGNI, SSR‑first rendering, explicit user actions, and client‑side validation priority.

