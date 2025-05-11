
# <img src="main/static/images/favicon.ico" alt="TWLKR Logo" width="20" style="vertical-align: middle;"/> TWLKR TMS System

> **Production URL:** https://twlkr-459107.du.r.appspot.com<br>
> *1. This system is designed for desktop use only, with all interfaces optimized for Korean language. The application uses KST (UTC+9) for all time-related operations.* <br>
> *2. For account access, please contact Sungyong Kim at TWLKR.* <br>
### Demo Video

[![데모 비디오](https://img.youtube.com/vi/4RFC88mS1Wk/0.jpg)](https://youtu.be/4RFC88mS1Wk)


## 1. Project Summary

The TWLKR TMS System is an enterprise application designed to streamline delivery operations through efficient order management and driver assignment. The system provides a centralized platform for tracking deliveries, managing dispatch operations, and facilitating handover communications between team members.

### Key Features:
- **Real-time delivery tracking** with ETA-based order management
- **Centralized driver assignment and contact management**
- **Two-level access control** (USER and ADMIN roles)
- **Handover communication system** with notice board functionality

## 2. Technical Architecture

### Technology Stack

| Layer | Technologies | Details |
|-------|--------------|---------|
| **Backend** | Python 3.12, FastAPI, Jinja2 | Server-side rendering (SSR) for initial page load with client-side rendering (CSR) for interactive elements |
| **Frontend** | HTML/CSS/JavaScript | Bootstrap/Tailwind for UI components with modular JS approach |
| **Database** | MySQL 8.0 | Deployed on Cloud SQL with Private IP connections |
| **Infrastructure** | Google App Engine (Flexible) | Custom runtime with Docker containerization |

### Security Implementation

The system employs multiple layers of security:

- **Network Security:**
  - Cloud Armor protection against DDoS and web attacks
  - Private IP connections to Cloud SQL
  - Firewall rules limiting access to authorized sources

- **Application Security:**
  - HSTS, X-Content-Type-Options, X-Frame-Options headers
  - SameSite=Lax cookies for CSRF protection
  - Server-side session validation for all protected routes
  - Comprehensive input validation (server-side and client-side)

- **Data Protection:**
  - Concurrent modification prevention through lock mechanism
  - Automatic timeout and release of locks after 5 minutes
  - Data encryption in transit (HTTPS enforced)

- **Authentication & Authorization:**
  - Role-based access control (USER/ADMIN)
  - Session-based authentication with secure cookies
  - Automatic redirection to login for unauthorized access attempts

## 3. User Scenarios

### Regular User (Dispatcher)

1. **Login**: User logs in with their credentials
2. **Dashboard View**: User accesses the dashboard to view all current deliveries
3. **Order Management**:
   - Filter orders by date range
   - Search for specific order numbers
   - View detailed information for any order
   - Update order status and driver information
4. **Handover Communication**:
   - Create handover notes for shift changes
   - Read important notices from administrators
   - View handover history for operational continuity

### Administrator User

Administrators have all regular user capabilities plus:

1. **User Management**:
   - View all system users
   - Create new user accounts
   - Manage user roles and permissions

2. **Advanced Order Management**:
   - Delete orders when necessary
   - Perform administrative overrides

3. **Notice Management**:
   - Post company-wide notices
   - Edit or delete any handover notes

---
 <div align="center">
  <img src="main/static/images/logo.png" alt="TWLKR Logo" width="350"/>
</div>

> *Project Planning & Oversight: Sungyoung Kim, TWLKR Operation Manager*
> 
> *Developed by: Jonghyeok Park, TWLKR Operation Team*  
