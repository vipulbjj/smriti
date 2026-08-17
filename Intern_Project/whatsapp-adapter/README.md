---
title: WhatsApp Adapter
emoji: 💬
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
---

# WhatsApp Adapter

A lightweight FastAPI service that bridges WhatsApp Business API webhooks with your application logic. It receives incoming messages from Meta's WhatsApp Cloud API, routes them through a configurable webhook handler, and sends replies back to users.

## Setup

1. Clone this repository and install dependencies locally:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your WhatsApp credentials (access token, phone number ID, verify token, etc.).

3. Run the server locally:

   ```bash
   uvicorn app:app --host 0.0.0.0 --port 7860
   ```

## Deployment to HuggingFace Spaces

This project is configured for deployment as a Docker Space on HuggingFace:

1. Create a new Space and select **Docker** as the SDK.
2. Push this repository to the Space (or connect your GitHub repo).
3. Set the required secrets/environment variables in the Space settings (WhatsApp API tokens, webhook verify token, etc.).
4. HuggingFace will build the Dockerfile and expose the app on port **7860**.

Once deployed, configure your WhatsApp webhook URL in the Meta Developer Console to point to your Space's public endpoint.
