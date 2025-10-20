# Library Management System

A Django 5.2 application that manages library operations, including catalog management, circulation workflows, notifications, dashboards, and a REST API.

## Features

- Role-aware access for administrators, librarians, and members
- Catalog management with categories, books, and copies
- Circulation for loans, reservations, and fines
- Notifications preferences and basic reporting dashboard
- REST API endpoints secured with DRF permissions
- Responsive Bootstrap 5 interface with HTTPS-ready dev server

## Local Development

1. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. Apply migrations (already included in the repo):
   ```powershell
   python manage.py migrate
   ```
3. Launch the development server over HTTPS (self-signed cert `local.crt`):
   ```powershell
   python manage.py runserver_plus --cert-file local.crt
   ```
   Use `http://127.0.0.1:8000/` for HTTP or accept the browser warning for `https://127.0.0.1:8000/`.

## Synthetic Data Seeder

Populate the database with 1000 books and loans, along with users and related entities:

```powershell
python manage.py seed_library
```

- Creates or tops up 1000 books (with multiple copies) and 1000 loans
- Adds member and librarian accounts as needed
- Generates reservations and fines for realistic circulation data
- Default password for generated accounts: `password123`
  - Admin account: `admin` / `password123`
  - Librarian accounts: `librarian001`, `librarian002`, ...
  - Member accounts: `member0001`, `member0002`, ...

You can adjust counts via flags such as `--books`, `--loans`, `--members`, and `--librarians`.

## Troubleshooting

- If you change `SECRET_KEY`, clear browser cookies to avoid `Session data corrupted` warnings.
- Static assets are served via Django’s staticfiles app when `DEBUG=True`; run `python manage.py collectstatic` before production deployment.
- The login redirect is role-aware: admins and librarians land on the reports dashboard, members land on the account overview.

## Next Steps

- Add automated tests for seeding and permissions.
- Extend the reporting dashboard with visualizations.
- Integrate notification sending (email/SMS) backends.
