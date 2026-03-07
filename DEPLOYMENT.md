# AWS Deployment Guide for Streamlit App

This guide outlines how to deploy your Streamlit application to AWS securely, ensuring API keys are provided as environment variables instead of hardcoded or placed in a `.env` file.

## Option 1: AWS App Runner (Recommended for Simplicity)

AWS App Runner provides a fast, simple way to deploy containerized web applications without managing servers.

### 1. Containerize or Connect GitHub
- **Source Code Repository:** Connect your GitHub repository to App Runner directly.
- Ensure the start command is `streamlit run app.py --server.port 8080` (App Runner uses port 8080 by default).

### 2. Setting Environment Variables
When configuring the App Runner service:
1. Go to the **Configure service** step.
2. Under **Service settings**, expand the **Environment variables** section.
3. Click **Add environment variable**.
4. Set the **Key** to `GROQ_API_KEY`.
5. Set the **Value** to your actual Groq API key (e.g., `gsk_...`).
6. *Optional*: For increased security, you can use **AWS Secrets Manager**, but plain environment variables are acceptable for straightforward deployments.

### 3. Deploy
- Complete the setup and deploy your service.
- App Runner will inject `GROQ_API_KEY` into your application's environment, where `os.environ.get("GROQ_API_KEY")` will pick it up seamlessly.

---

## Option 2: AWS EC2 (More Control)

If you are running the app on a traditional EC2 instance (e.g., Amazon Linux 2023 or Ubuntu).

### 1. Setting Up the Instance
1. SSH into your instance.
2. Clone your repository: `git clone <your-repo-url>`
3. Install dependencies: `pip install -r requirements.txt`

### 2. Setting Environment Variables
Do **not** create a `.env` file or commit it to your repository. Instead, pass the environment variables to the process.

#### Temporary Session (For Testing):
```bash
export GROQ_API_KEY="your_actual_api_key"
streamlit run app.py
```

#### Persistent Setup (Using Systemd):
If you are using `systemd` to run your Streamlit app as a background service:
1. Open your service file (e.g., `/etc/systemd/system/streamlit.service`).
2. Add the `Environment=` directive under the `[Service]` block:
```ini
[Unit]
Description=Streamlit App

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/your-app-repo
Environment="GROQ_API_KEY=your_actual_api_key"
ExecStart=/usr/local/bin/streamlit run app.py
Restart=always

[Install]
WantedBy=multi-user.target
```
3. Reload systemd and restart the service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart streamlit
```

## Security Reminders!
- **Never** commit `.env` or any file containing `GROQ_API_KEY` to Git.
- **Always** verify your `.gitignore` is active and ignoring `.env`.
- Ensure your security groups only open the necessary ports (like 8501 for default Streamlit, or 80/443 if using a load balancer/reverse proxy).
