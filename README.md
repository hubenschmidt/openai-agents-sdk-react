# openai-agents-sdk-react

Bootstrap that runs:

- **OpenAI Agents SDK**
- **FastAPI WebSocket server**
- **React client (Next.js)**

Everything is wired together with **Docker Compose**.

---

## 0) Prerequisites

- Docker & Docker Compose
- (Optional) Node 18+ if you want to run the client locally outside Docker

---

## 1) Environment variables

Create a root `.env` from the example and fill any `# CHANGEME` values:

```bash
cp .env.example .env
```

Set your OpenAI API key in `modules/agent/.env`:

```
OPENAI_API_KEY=sk-...
```

---

## 2) Start everything

```bash
docker compose up
```

## 3) Test everything is working

- Open http://localhost:3001
- Send a message. You should see **User** bubble on the **right**, **Bot** streaming response on the **left**

## 4) What's running (ports)

| Service                  | URL / Port             | Notes                                    |
| ------------------------ | ---------------------- | ---------------------------------------- |
| FastAPI WebSocket server | ws://localhost:8000/ws | React client connects here for streaming |
| React client (Next.js)   | http://localhost:3001  | Chat UI that talks to the WS server      |
