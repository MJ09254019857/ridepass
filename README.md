# RidePass – Django Web Application

Android-Based Mobile Ticketing Application for Public Transportation
By: Acedera, Oval, Urtua

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv env
env\Scripts\activate        # Windows
source env/bin/activate     # macOS/Linux

# 2. Install Django
pip install django

# 3. Apply database migrations
python manage.py migrate

# 4. Seed sample routes
python manage.py seed_routes

# 5. Create admin account (optional)
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

## Pages
- `/`              Landing Page
- `/login/`        Login Page
- `/register/`     Register Page
- `/dashboard/`    Dashboard (login required)
- `/topup/`        Top Up Wallet
- `/routes/`       Browse & Buy Tickets
- `/tickets/`      My Tickets
- `/history/`      Transaction History
- `/admin/`        Django Admin Panel

## Test Admin Account
- Username: admin
- Password: admin123
