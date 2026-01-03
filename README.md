**Kharchabook — Cloud Expense Tracker (AWS)**  
Kharchabook is a cloud-hosted expense tracking and budgeting web app that supports manual expense entry and receipt scanning (OCR) to auto-extract expense details.

**Features**
- User authentication (login-protected routes)
- Add manual expenses
- Upload receipt images and extract data via OCR
- Monthly budget + category limits
- Analytics/summary views
- Health endpoint for load balancer checks: `GET /health` returns `200`

**Tech Stack**
- Backend: Python Flask + Gunicorn
- Reverse proxy: Nginx
- Deployment: Ubuntu on AWS EC2, behind AWS Application Load Balancer (ALB)
- OCR: Amazon Textract (AnalyzeExpense) (if enabled)

**Architecture (High-level)**
- ALB routes incoming traffic to EC2 targets (HTTP/80 or HTTPS/443)
- Nginx reverse proxies requests to Gunicorn on `127.0.0.1:5000`
- Flask app handles auth, expenses, receipts, and UI/API
- `/health` is used for ALB target group health checks (expects HTTP 200)

**Local Development**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
Open: http://127.0.0.1:5000

Production (EC2) Deployment Notes

Systemd service (Gunicorn)

bash
sudo systemctl restart kharchabook
sudo systemctl status kharchabook --no-pager
sudo journalctl -u kharchabook -n 100 --no-pager
Nginx

bash
sudo systemctl restart nginx
sudo nginx -t
ALB Health Check
Configure Target Group health check:

Path: /health

Success code: 200

CI/CD (Quick)
A simple GitHub Actions workflow can deploy to EC2 by SSH:

Pull latest code

Install requirements

Restart kharchabook + nginx

Verify /health

Troubleshooting

/scan-receipt redirecting to /login is normal (protected route).

If using multiple EC2 instances behind ALB, ensure both instances have identical config (especially SECRET_KEY) to avoid session inconsistency.

License
Add your license (e.g., MIT) or remove this section.

