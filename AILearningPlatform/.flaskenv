# Flask Environment Variables
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Database Configuration
DATABASE_URL=sqlite:///learnify.db

# Session Configuration
SESSION_SECRET=dev_secret_key_please_change_in_production

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Rate Limiting
RATELIMIT_DEFAULT=200 per day;50 per hour
