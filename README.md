<<<<<<< HEAD

# 🚚 TWLKR Real-Time Delivery Control System — README

=======
# 🚚 TWLKR Real-Time Delivery Control System — README

>>>>>>> origin/main
> **This repository is under active development. The production URL will be shared after the server is deployed in May 2025.**

---

## 1. Project Overview & Architecture

### 1‑1. Purpose

- **Real‑time order management** — query and control delivery orders based on ETA (Estimated Time of Arrival).
- **Efficient dispatch** — unified interface for assigning couriers and updating delivery states.
- **Role‑based access** — separate feature sets for **USER** and **ADMIN** accounts.

### 1‑2. Technology Stack

| Layer            | Technologies                                           | Notes                                |
| ---------------- | ------------------------------------------------------ | ------------------------------------ |
| **Backend**      | Python 3.12 · FastAPI · Jinja2 (SSR)                   | Single application container         |
| **Frontend**     | HTML + CSS · Modular JavaScript (minimal global scope) | CSR interaction modules              |
| **Database**     | MySQL 8.0 (`init-db.sql`) · Cloud SQL                  | Private IP · IAM DB Auth             |
| **Infrastructure** | Docker → Google App Engine Flexible (`runtime: custom`) | Cloud Armor · Firewall               |

### 1‑3. Request Flow (Login → SSR → CSR)

```mermaid
flowchart TD
    A["Client Browser"] --> B{Session or Cookie?}
    B -- "No"  --> C["Redirect to /login"]
    B -- "Yes" --> D["SSR Render HTML"]
    D --> A
    A --> E["Client‑side JS (CSR) API Calls"]
```

---

## 2. Deployment Architecture & Security

### 2‑1. Infrastructure Overview

```mermaid
flowchart TD
    subgraph GCP
        CA["Cloud Armor / TLS"]
        FW["Firewall Allow‑list"]
        GAE["GAE Flex (Docker Container)"]
        Log["Logging & Monitoring"]
        SQL["Cloud SQL (MySQL 8.0)"]
        CA --> FW --> GAE --> Log
        GAE --> SQL
    end
```

### 2‑2. Application Security Controls

| Area                | Measures                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------- |
| **GAE Flex**        | Cloud Armor · Firewall, HSTS, `X-Content-Type-Options`, `X-Frame-Options`                   |
| **CORS**            | Allow‑list only the minimum required domains                                                |
| **Sessions**        | Server‑side sessions, `HttpOnly` + `Secure` cookies, automatic logout on expiration         |
| **Cloud SQL**       | Private IP, SSL/TLS, IAM DB Auth, automated backups, least‑privilege parameters             |
| **Input Validation**| Central server‑side validation with client‑side assistance; protection against SQLi and XSS |
| **Logging**         | No PII stored; unified JSON schema `{success, error_code, message}`                         |

### 2‑3. Deployment Pipeline
<<<<<<< HEAD
=======

1. Build a single **Dockerfile** and deploy with `gcloud app deploy` (GAE Flex).
2. Manage secrets and configuration through environment variables.
3. For local development, connect to Cloud SQL via **Cloud SQL Auth Proxy**.

---

## 3. Key Features (User Perspective)

### 3‑1. Dashboard

- **Real‑time delivery order list**
  ![스크린샷 2025-04-29 140553](https://github.com/user-attachments/assets/92c132a8-9a72-4cd9-bf37-03c30e0e789e)

- **Create new delivery orders**
  ![스크린샷 2025-04-29 140601](https://github.com/user-attachments/assets/e6b1a63b-da94-48cf-b888-2a3551d7d448)

- **Assign couriers and update delivery status (for dispatch operators)**
  ![스크린샷 2025-04-29 140643](https://github.com/user-attachments/assets/e7d3d3bb-962c-4d5e-9bb2-8542e79bb34e)
  ![스크린샷 2025-04-29 140624](https://github.com/user-attachments/assets/06f6ef94-788f-4702-9206-b39fd6b29888)

- **View detailed order information**
  ![스크린샷 2025-04-29 140607](https://github.com/user-attachments/assets/461ec753-4693-477d-84d2-4287a0923782)

- **Basic data visualizations (e.g., order volumes, courier workload)**
  ![스크린샷 2025-04-29 140734](https://github.com/user-attachments/assets/28ce2a44-cfe4-4da4-a1bd-cf899976191c)

---

> For questions or suggestions, please open an issue in the **Issues** tab.
>>>>>>> origin/main

1. Build a single **Dockerfile** and deploy with `gcloud app deploy` (GAE Flex).
2. Manage secrets and configuration through environment variables.
3. For local development, connect to Cloud SQL via **Cloud SQL Auth Proxy**.
