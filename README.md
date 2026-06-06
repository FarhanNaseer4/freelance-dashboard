# Freelance OS

A modern Django dashboard for freelancers managing orders, clients, milestones, hourly work, payments, follow-ups, and revenue across Fiverr, Upwork, and direct clients.

Freelance OS works as a personal CRM, lightweight project management system, and revenue tracker in one place. It is designed for a solo freelancer who wants a clear daily command center instead of scattered spreadsheets.

## Highlights

- Client CRM for Fiverr, Upwork, and direct clients
- Project tracking for fixed-price, milestone-based, and hourly contracts
- Command-center dashboard with active work, follow-ups, revenue, activity, and quick actions
- Kanban-style project pipeline
- Completed project archive
- Follow-up inbox for daily work
- Milestone manager with current, completed, paid, and pending milestones
- Hourly time logs with cleared and uncleared earnings
- Payment tracking with contract payments, Fiverr tips, and Upwork bonuses
- Platform fee calculations:
  - Fiverr: 20%
  - Upwork: 10%
  - Direct: 0%
- Gross, net, and fee-aware monthly revenue
- Client health view
- Calendar for deliveries, follow-ups, and milestone deadlines
- Analytics for revenue by month, platform, project type, and client
- CSV/XLSX import for clients and projects
- CSV/XLSX project export
- JSON backup export
- Django admin customization
- Login-protected dashboard
- Responsive Tailwind UI with dark mode

## Tech Stack

- Python 3.11+
- Django
- PostgreSQL
- Tailwind CSS via CDN
- Alpine.js
- Chart.js
- Lucide icons
- WhiteNoise
- Gunicorn
- OpenPyXL

## Project Structure

```text
config/      Django settings, URLs, WSGI/ASGI
core/        Shared auth helpers, analytics, template tags
clients/     Client CRM models, views, forms, admin
projects/    Projects, milestones, time logs, notes, activity, pipeline
payments/    Payment model, categories, platform fee calculations
dashboard/   Dashboard, analytics, calendar, follow-up inbox
imports/     CSV/XLSX import and JSON backup export
templates/   Server-rendered UI templates
```

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Generate a Django secret key:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Update `.env`:

```env
DJANGO_SECRET_KEY=replace-with-generated-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/freelance_dashboard
```

Create a local PostgreSQL database:

```sql
CREATE DATABASE freelance_dashboard;
```

Run migrations:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Local SQLite Mode

For quick local use without PostgreSQL:

```env
USE_SQLITE=True
SQLITE_NAME=C:\Users\YOUR_USER\AppData\Local\Temp\freelance_dashboard.sqlite3
```

Then run:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Seed Data

Demo data:

```powershell
python manage.py seed_demo_data
```

Current order seed data:

```powershell
python manage.py seed_current_orders
```

The current order seed includes:

- Lindsey
- Lauren
- Brandon
- Ayo Peter
- Ben Webb
- Miodrag
- Boris Z

## Main Pages

```text
/                         Command center dashboard
/projects/                Active projects table
/projects/pipeline/       Kanban project pipeline
/projects/completed/      Completed project archive
/projects/new/            Add project
/clients/                 Clients
/clients/new/             Add client
/clients/health/          Client health view
/follow-ups/              Daily follow-up inbox
/calendar/                Calendar
/payments/                Payments
/analytics/               Revenue analytics
/imports/                 Imports and exports
/admin/                   Django admin
```

## Contract Workflows

### Fixed Price

Use for one-budget projects.

- Add budget
- Track payment
- Track tips/bonus
- Mark delivered or completed
- Completed projects are moved to the completed archive

### Milestone Based

Use for projects with multiple paid stages.

- Add total budget
- Add milestones
- Track current milestone
- Mark milestone complete
- Mark milestone paid
- Milestone payment creates a received contract payment

### Hourly

Use for hourly work.

- Add hourly rate
- Log hours worked
- Record cleared payments
- Track hourly earnings
- Track cleared and uncleared hours
- Track remaining/uncleared balance

## Revenue Logic

Payment categories:

- `Contract Payment`
- `Tip`
- `Bonus`

Platform fee rules:

- Fiverr: 20%
- Upwork: 10%
- Direct: 0%

Dashboard revenue:

```text
Gross = received payment amount
Fee = gross * platform rate
Net = gross - fee
```

Tips and bonuses count as revenue, but do not reduce the remaining project contract balance.

Monthly revenue is calculated using `date_received` from the 1st day of the current month through the end of that month.

## Imports And Exports

Project exports:

```text
/projects/export/csv/
/projects/export/excel/
```

Backup export:

```text
/imports/backup.json
```

Import page:

```text
/imports/
```

Client CSV columns:

```csv
name,platform,email,company,notes
```

Project CSV columns:

```csv
client,project,platform,contract_type,project_type,budget,status,priority,next_action
```

Valid platform values:

```text
Fiverr
Upwork
Direct
```

## Deploy To Render

This project includes:

- `build.sh`
- `runtime.txt`
- `gunicorn`
- WhiteNoise static file support
- production settings

### 1. Push To GitHub

```powershell
git init
git add .
git commit -m "Initial freelance dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/freelance-dashboard.git
git push -u origin main
```

### 2. Create Render Postgres

In Render:

1. New
2. Postgres
3. Choose your plan
4. Copy the internal database URL

Free Render Postgres databases are useful for testing, but they expire after 30 days and do not include backups.

### 3. Create Render Web Service

In Render:

1. New
2. Web Service
3. Connect the GitHub repo
4. Runtime: Python 3
5. Branch: `main`

Build command:

```bash
bash build.sh
```

Start command:

```bash
python manage.py migrate && gunicorn config.wsgi:application
```

Environment variables:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=generate-a-secure-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-service-name.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-service-name.onrender.com
DATABASE_URL=your-render-internal-postgres-url
```

Do not set `USE_SQLITE=True` on Render.

### 4. Create Admin User On Render

After deploy succeeds, open Render Shell:

```bash
python manage.py createsuperuser
```

Then visit:

```text
https://your-service-name.onrender.com/admin/login/
```

## Production Notes

- Dashboard pages require login.
- Use PostgreSQL in production.
- Do not commit `.env`.
- Use a strong `DJANGO_SECRET_KEY`.
- Set `DJANGO_DEBUG=False` on Render.
- Add your Render domain to `DJANGO_ALLOWED_HOSTS`.
- Add your Render origin to `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Free Render services may spin down after inactivity.
- Free Render Postgres expires after 30 days.

## Tests

Run:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Current test coverage includes:

- model calculations
- platform fee calculations
- dashboard metrics
- project create/edit/archive
- pipeline rendering
- payment and milestone actions
- import validation
- seed commands
- protected page rendering

## License

Private personal project unless you choose to add a license.
