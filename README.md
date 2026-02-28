# Consumer Insight Portal

A professional, corporate-grade Django application for hosting market research tasks with seamless offer integration and conversion tracking.

## 🎯 Project Overview

The Consumer Insight Portal is a Django-based platform that fetches high-payout market research offers from CPAGrip and presents them in a professional, trustworthy environment. The application features a minimalist UI with "Trust Blue" branding, comprehensive conversion tracking, and a powerful admin dashboard.

## ✨ Key Features

### User-Facing Features
- **Professional Landing Page**: Clean, corporate-grade introduction with trust indicators
- **Available Offers List**: Browse verified market research opportunities
- **Task Environment**: Seamless iframe integration for completing offers
- **Verification Progress**: 3-step progress bar guiding users through tasks
- **Responsive Design**: Mobile-first design using Tailwind CSS

### Admin Features
- **Revenue Monitor Dashboard**: Real-time earnings, conversions, and EPC tracking
- **Offer Management**: Approve, reject, and feature offers with manual override
- **Lead Inspection**: View detailed conversion data including IP, device type, and user agent
- **Sync Control**: Manual sync triggers to fetch new offers from CPAGrip
- **Conversion Analytics**: Daily revenue charts and top-performing offers

### Technical Features
- **CPAGrip API Integration**: Automatic offer fetching with tracking_id injection
- **Global Postback Callback**: Conversion tracking via CPAGrip callbacks
- **Bot Detection**: Automated detection and flagging of bot traffic
- **Device Detection**: Mobile, tablet, and desktop device identification
- **Secure Iframe Sandbox**: Safe embedding of external offers

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Virtual environment (venv)

### Installation

1. **Activate Virtual Environment**
```bash
source venv/bin/activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment Variables**
Edit `.env` file with your settings:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
ALLOWED_HOSTS=localhost,127.0.0.1

# CPAGrip API Configuration
CPAGRIP_PRIVATE_KEY=655da6911e93776a7d5fc6fc1f1ea46e
CPAGRIP_API_URL=https://www.cpagrip.com/api/v2/offers.php
MIN_PAYOUT_THRESHOLD=0.50
ALLOWED_COUNTRIES=US
OFFER_TYPES=Email Submit,Zip Submit,Email/Zip Submit
```

4. **Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create Superuser** (if not already created)
```bash
python manage.py createsuperuser
```

Default credentials:
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123`

6. **Run Development Server**
```bash
python manage.py runserver
```

7. **Access the Application**
- Frontend: http://localhost:8000
- Admin Panel: http://localhost:8000/admin

## 📊 CPAGrip Integration

### API Configuration

The application automatically fetches offers from CPAGrip API using your private key. Offers are filtered by:

- **Minimum Payout**: Configurable threshold (default: $0.50)
- **Countries**: US-only offers
- **Offer Type**: Email/Zip Submit offers only

### Tracking ID Flow

1. User accesses task page → Django generates unique tracking_id
2. tracking_id is appended to offer URL via iframe
3. CPAGrip sends callback to `/callback/` with tracking_id
4. Conversion status is updated in database
5. Revenue is tracked in admin dashboard

### Callback URL

Configure your CPAGrip Global Postback URL:
```
https://yourdomain.com/callback/
```

Expected parameters:
- `tracking_id`: Unique identifier for conversion
- `payout`: Offer payout amount (optional)
- `offer_id`: CPAGrip offer ID (optional)
- `status`: Conversion status (completed/failed, optional)

## 🎨 UI/UX Design

### Trust Blue Color Scheme
- Primary: `#0086ff` (Bright Blue)
- Secondary: `#003e91` (Deep Navy)
- Light: `#e0effe` (Pale Blue)
- Dark: `#003573` (Midnight Blue)

### Design Principles
- **Minimalist**: Clean, uncluttered interface
- **Professional**: Government/banking aesthetic
- **Trustworthy**: Clear typography, security indicators
- **Responsive**: Mobile-first approach
- **Accessible**: High contrast, readable fonts

## 🔧 Admin Dashboard

### Revenue Monitor Dashboard
Access: http://localhost:8000/admin/revenue-dashboard/

Features:
- Today's revenue and conversions
- Weekly overview with charts
- All-time statistics
- Top performing offers
- Device type distribution
- Earnings Per Click (EPC) calculation

### Offer Management
Access: http://localhost:8000/admin/insights/cachedoffer/

Features:
- **Status Workflow**: pending → live/rejected
- **Featured Offers**: Pin offers to top of listings
- **Display Order**: Manual ranking control
- **Bulk Actions**: Approve, reject, or feature multiple offers
- **Review Queue**: All new offers start in "pending" status

### Conversion Tracking
Access: http://localhost:8000/admin/insights/conversiontracking/

Features:
- View all conversions with detailed metadata
- Filter by status, device type, or date
- Search by tracking ID, IP, or offer name
- Mark conversions as completed/failed
- Flag suspicious conversions for review
- Admin notes for manual review

### Sync Controls
Access: http://localhost:8000/admin/sync-offers/

Manually trigger offer sync from CPAGrip API. New offers are added to review queue for approval.

## 🛡️ Security Features

### Bot Detection
Automated detection of bot traffic based on user agent patterns:
- Common bot keywords (bot, crawler, spider, etc.)
- Headless browser detection
- Known scraping tools

### Iframe Security
Sandbox attributes for safe embedding:
- `allow-same-origin`: Prevent cross-origin issues
- `allow-scripts`: Enable offer functionality
- `allow-forms`: Allow form submissions
- `allow-popups`: Enable popups if needed
- `allow-presentation`: Enable fullscreen API

### Data Privacy
- IP address logging for lead inspection
- User agent tracking for device detection
- Referrer tracking for source analysis
- Secure HTTPS recommended for production

## 📁 Project Structure

```
affiliate/
├── affiliate/              # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py           # URL routing
│   └── wsgi.py
├── insights/              # Main application
│   ├── admin.py           # Admin configuration
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py           # App URLs
│   ├── services.py        # CPAGrip API integration
│   └── utils.py          # Helper functions
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── home.html        # Landing page
│   ├── offers.html       # Offers list
│   ├── task.html        # Task environment
│   ├── verification.html # Progress bar
│   ├── 404.html        # Error page
│   └── 500.html        # Error page
├── templates/admin/        # Admin templates
│   └── revenue_dashboard.html
├── static/               # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── requirements.txt        # Python dependencies
├── .env                 # Environment variables
├── manage.py            # Django management script
└── README.md            # This file
```

## 🔍 Database Models

### CachedOffer
- Offer details (name, payout, description)
- Publication control (status, featured, display_order)
- Geographic targeting (countries)
- Metadata (timestamps, review info)

### ConversionTracking
- Tracking ID for conversion correlation
- User information (IP, device type, user agent)
- Status tracking (pending, completed, failed, flagged)
- Timestamps (created, completed, updated)

### AdminSettings
- Key-value configuration storage
- Dynamic settings management

## 🚢 Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure production database (PostgreSQL)
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up HTTPS/SSL
- [ ] Configure CPAGrip callback URL
- [ ] Set up static file serving
- [ ] Configure logging
- [ ] Set up monitoring

### Recommended Hosting
- **Heroku**: Easy deployment, PostgreSQL addon
- **DigitalOcean**: Full control, affordable
- **AWS**: Scalable, enterprise-grade
- **Railway**: Simple, modern deployment

## 📈 Monitoring & Analytics

### Admin Dashboard Metrics
- Daily/weekly/monthly revenue
- Conversion count and rate
- Earnings Per Click (EPC)
- Top-performing offers
- Device type distribution
- Daily revenue charts

### Conversion Tracking
- Real-time callback processing
- Lead inspection (IP, device, user agent)
- Status tracking (pending → completed/failed)
- Admin notes for manual review

## 🤝 Support

For issues or questions:
- Email: support@consumerinsightportal.com
- Documentation: See this README
- Admin Panel: http://localhost:8000/admin

## 📝 License

This project is proprietary software. All rights reserved.

## 🙏 Acknowledgments

- Django Framework
- CPAGrip API
- Tailwind CSS
- Google Fonts (Inter)

---

**Built with Django 5.0.6** | **Professional Market Research Platform**