Kharchabook — Cloud Expense Tracker (AWS)
Kharchabook is a cloud-hosted expense tracking and budgeting web app that supports manual expense entry and receipt scanning (OCR) to auto-extract expense details. It is deployed on AWS using a 3‑tier approach with EC2 (app), a database layer, and object storage for receipt images.

Features
User authentication (login-protected routes)

Add manual expenses

Upload receipt images and extract data via OCR

Monthly budget + category limits

Analytics/summary views

Health endpoint for load balancer checks: GET /health returns 200

Tech Stack
Backend: Python Flask + Gunicorn

Reverse proxy: Nginx

Deployment: Ubuntu on AWS EC2, behind AWS Application Load Balancer (ALB)

OCR: Amazon Textract (AnalyzeExpense) (if enabled in your setup)
​

Architecture (High-level)
ALB routes incoming traffic to EC2 targets (HTTP/80 or HTTPS/443)

Nginx reverse proxies requests to Gunicorn on 127.0.0.1:5000

Flask app handles auth, expenses, receipts, and UI/API

/health is used for ALB target group health checks (expects HTTP 200)
​

Local Development
bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
Then open:

http://127.0.0.1:5000

Production (EC2) Deployment Notes
Systemd service (Gunicorn)
A systemd unit runs Gunicorn as a background service.

Common commands:

bash
sudo systemctl restart kharchabook
sudo systemctl status kharchabook --no-pager
sudo journalctl -u kharchabook -n 100 --no-pager
Nginx
Nginx listens on port 80 and proxies to Gunicorn on 127.0.0.1:5000.

Common commands:

bash
sudo systemctl restart nginx
sudo nginx -t
ALB Health Check
Configure Target Group health check:

Path: /health

Expected success code: 200
​

CI/CD (Quick)
A simple GitHub Actions workflow can deploy to EC2 by SSH:

pull latest code

install requirements

restart kharchabook + nginx

verify /health

(Workflow file can be added at .github/workflows/deploy.yml.)

Troubleshooting
If /scan-receipt redirects to /login, it’s normal (route is protected).

If you run multiple EC2 instances behind ALB, ensure both instances have identical config (especially SECRET_KEY) to avoid session inconsistency.

License
Specify your license here (e.g., MIT) or remove this section.

If you tell your repo name, AWS services actually used (RDS? S3? Textract?), and whether it’s Flask-only or has a separate frontend, I can tailor the README exactly to match your final architecture.
