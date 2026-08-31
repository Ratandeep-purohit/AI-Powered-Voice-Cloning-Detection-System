# Technology Stack

## 1. Technology Stack Overview

This technology stack is selected to balance rapid Smart India Hackathon MVP development with reliable AI/ML capabilities, real-time functionality, professional user interfaces, clean architecture, and future scalability. The initial implementation prioritizes a focused core system and avoids unnecessary infrastructure complexity.

| Layer | Primary Technologies | Status |
|---|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide React, React Router, Axios, Recharts, WebSocket | MVP / Core |
| Backend | Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic | MVP / Core |
| AI / Machine Learning | PyTorch, torchaudio, librosa, NumPy, SciPy, PyDub, WebRTC VAD, pretrained voice anti-spoofing model | MVP / Core |
| AI Workflow and Security Copilot | LangChain, LangGraph, LLM API, Pydantic Structured Output | MVP / Core, where feasible |
| Risk Scoring | Python, rule-based scoring, weighted risk factors, contextual risk analysis, deterministic policy validation | MVP / Core |
| Database | PostgreSQL | MVP / Core |
| Cache and Real-Time State | Redis | Phase 2 / Optional for MVP |
| Real-Time Communication | FastAPI WebSockets; WebRTC | WebSockets: MVP / Core; WebRTC: Future Enhancement |
| Authentication and Security | JWT, RBAC, Argon2, HTTPS / TLS, environment variables, API rate limiting, input validation, audit logging | MVP / Core |
| API and Integration | REST API, WebSocket API; gRPC, webhooks, SDKs | REST/WebSockets: MVP / Core; others: Future |
| DevOps and Deployment | Docker, Docker Compose, Git, GitHub; Nginx, Kubernetes | Docker/Docker Compose: MVP / Core; others: Future Production |
| Testing | pytest, pytest-asyncio, httpx, Vitest, React Testing Library, Postman or Bruno | MVP / Core |
| Monitoring and Logging | Python logging, structured logs, application error logging; Prometheus, Grafana | Basic logging: MVP / Core; others: Future |

## 2. Architecture Principles

- **MVP-first development:** Focus on the core voice detection, risk scoring, alerting, and dashboard capabilities before optional infrastructure.
- **Avoid unnecessary microservices:** Keep the MVP implementation focused and avoid unnecessary distributed-system complexity.
- **Python-first ML integration:** Use Python for backend services, audio analysis orchestration, ML model integration, and risk scoring.
- **Real-time communication:** Use WebSockets to deliver live detection, risk score, alert, and dashboard updates.
- **Security by design:** Apply authentication, authorization, encryption, input validation, rate limiting, and audit logging from the outset.
- **Modular architecture:** Keep voice detection, risk scoring, alerts, integrations, and the Security Copilot modular.
- **Future scalability:** Retain clear paths to Redis, Nginx, Kubernetes, gRPC, webhooks, SDKs, and production monitoring when needed.
- **Deterministic security actions:** Critical security or transaction actions remain controlled by backend policy and rule validation, not by an LLM.

## 3. Frontend

The frontend provides the security analyst dashboard, live call monitoring, real-time risk-score visualization, synthetic-voice detection results, alert management, incident investigation, risk trend visualization, Security Copilot interface, and administrative interfaces.

| Technology | Purpose | Status |
|---|---|---|
| React | Build the frontend user interface and dashboard. | MVP / Core |
| TypeScript | Provide typed frontend development. | MVP / Core |
| Vite | Support frontend development and build tooling. | MVP / Core |
| Tailwind CSS | Provide UI styling. | MVP / Core |
| shadcn/ui | Provide reusable UI components. | MVP / Core |
| Lucide React | Provide interface icons. | MVP / Core |
| React Router | Manage frontend routing. | MVP / Core |
| Axios | Support API communication. | MVP / Core |
| Recharts | Visualize risk trends and related dashboard data. | MVP / Core |
| WebSocket | Receive real-time updates in the frontend. | MVP / Core |

## 4. Backend

The backend provides REST APIs, WebSocket endpoints, authentication and authorization, database access, audio analysis orchestration, ML model integration, risk scoring, alert generation, audit logging, and AI workflow orchestration.

| Technology | Purpose | Status |
|---|---|---|
| Python | Primary backend language and ML integration language. | MVP / Core |
| FastAPI | Implement REST APIs and WebSocket endpoints. | MVP / Core |
| Uvicorn | Run the FastAPI application. | MVP / Core |
| Pydantic | Provide request, response, and structured-data validation. | MVP / Core |
| SQLAlchemy | Provide database access. | MVP / Core |
| Alembic | Manage database migrations. | MVP / Core |

## 5. AI and Machine Learning

### 5.1 Primary Framework and Audio Processing

| Technology | Purpose | Status |
|---|---|---|
| PyTorch | Primary machine learning framework. | MVP / Core |
| torchaudio | Audio processing for the ML pipeline. | MVP / Core |
| librosa | Audio analysis and feature extraction. | MVP / Core |
| NumPy | Numerical processing. | MVP / Core |
| SciPy | Scientific and signal-processing support. | MVP / Core |
| PyDub | Audio manipulation. | MVP / Core |
| WebRTC VAD | Voice activity detection. | MVP / Core |

### 5.2 Detection Model Strategy

The system uses a pretrained voice anti-spoofing or synthetic voice detection model rather than training a large model from scratch during the hackathon.

### 5.3 Conceptual ML Pipeline

```text
Audio Input
    ↓
Audio Chunking
    ↓
Voice Activity Detection
    ↓
Noise Handling / Audio Normalization
    ↓
Feature Extraction
    ↓
Pretrained Voice Anti-Spoofing Model
    ↓
Synthetic Voice Probability
    ↓
Risk Scoring Engine
```

## 6. AI Workflow and Security Copilot

The project includes an AI-powered Security Copilot and workflow orchestration layer.

| Technology | Purpose | Status |
|---|---|---|
| LangChain | Support AI workflow and Security Copilot capabilities. | MVP / Core, where feasible |
| LangGraph | Orchestrate Security Copilot workflows. | MVP / Core, where feasible |
| LLM API | Provide natural-language reasoning and assistance. | MVP / Core, where feasible |
| Pydantic Structured Output | Produce structured recommendations. | MVP / Core, where feasible |

Primary Security Copilot use cases include:

- Explaining why a voice or call was flagged.
- Generating security incident summaries.
- Analyzing contextual risk information.
- Recommending verification actions.
- Assisting security analysts with natural-language investigation.
- Generating structured recommendations.

The LLM is an advisory and reasoning component. It must not directly execute critical security or transaction actions. The controlled decision path is:

```text
LLM / LangGraph Recommendation
    ↓
Policy and Rule Validation
    ↓
Authorized Backend Action
```

If LLM integration creates unnecessary implementation complexity, the Security Copilot may be implemented as a modular feature while keeping the core voice detection and risk engine independent.

## 7. Risk Scoring and Decision Engine

The risk scoring engine is implemented in Python and remains independent of the LLM.

| Component | Purpose | Status |
|---|---|---|
| Rule-Based Risk Scoring | Calculate risk using defined rules. | MVP / Core |
| Weighted Risk Factors | Weight the signals used in risk assessment. | MVP / Core |
| Contextual Risk Analysis | Incorporate contextual information into scoring. | MVP / Core |
| Deterministic Policy Validation | Validate critical decisions through deterministic backend policies. | MVP / Core |

Risk inputs include:

- Synthetic voice probability.
- Audio quality indicators.
- Voice consistency indicators.
- Caller information.
- Caller reputation.
- Transaction context.
- Historical risk indicators.

The engine outputs a risk score from 0–100 and one of the following risk levels:

- SAFE
- LOW
- MEDIUM
- HIGH
- CRITICAL

## 8. Database

PostgreSQL is the primary database for users, organizations, calls, audio analysis results, risk scores, alerts, alert actions, and audit logs.

Suggested logical entities are:

- `users`
- `organizations`
- `calls`
- `audio_segments`
- `voice_analyses`
- `risk_scores`
- `alerts`
- `alert_actions`
- `audit_logs`

The detailed database schema is documented separately in `docs/DATABASE.md`.

## 9. Cache and Real-Time State

Redis is optional for the MVP and is a Phase 2 technology. Potential responsibilities include:

- Active call state.
- Temporary risk-score caching.
- Real-time session state.
- WebSocket scaling.
- Rate limiting.
- Temporary analysis results.

The MVP should function correctly without Redis before this additional infrastructure is introduced.

## 10. Real-Time Communication

| Technology | Use | Status |
|---|---|---|
| FastAPI WebSockets | Live detection updates, live risk-score updates, alert notifications, dashboard updates, and analysis progress. | MVP / Core |
| WebRTC | Browser-based live audio streaming and low-latency audio communication. | Future Enhancement |

## 11. Authentication and Security

| Technology / Approach | Purpose | Status |
|---|---|---|
| JWT | Authentication token handling. | MVP / Core |
| Role-Based Access Control (RBAC) | Control access by assigned role. | MVP / Core |
| Argon2 password hashing | Password hashing. | MVP / Core |
| HTTPS / TLS | Protect communications. | MVP / Core |
| Environment Variables | Manage configuration and sensitive settings. | MVP / Core |
| API Rate Limiting | Limit API abuse. | MVP / Core |
| Input Validation | Validate application inputs. | MVP / Core |
| Audit Logging | Record security-relevant activity. | MVP / Core |

Suggested roles are:

- `SUPER_ADMIN`
- `ADMIN`
- `SECURITY_ANALYST`
- `OPERATOR`
- `AUDITOR`

The detailed security design is documented separately in `docs/SECURITY.md`.

## 12. API and Integration

| Technology | Purpose | Status |
|---|---|---|
| REST API | Primary MVP application integration API. | MVP / Core |
| WebSocket API | Deliver real-time application updates. | MVP / Core |
| gRPC | Enterprise integration. | Future |
| Webhooks | Enterprise event delivery. | Future |
| SDKs | Partner and platform integration. | Future |

Detailed endpoint documentation is maintained in `docs/API.md`.

## 13. DevOps and Deployment

### 13.1 Development and MVP

| Technology | Purpose | Status |
|---|---|---|
| Docker | Containerize application components. | MVP / Core |
| Docker Compose | Run the MVP service stack. | MVP / Core |
| Git | Version control. | MVP / Core |
| GitHub | Source-code hosting and collaboration. | MVP / Core |

Expected Docker services are:

- `frontend`
- `backend`
- `PostgreSQL`

Redis may be added later.

### 13.2 Production and Future

| Technology | Purpose | Status |
|---|---|---|
| Nginx | Production deployment component. | Production |
| Kubernetes | Container orchestration and horizontal scaling. | Future Scalability |

Kubernetes complexity is not introduced into the initial hackathon MVP.

## 14. Testing

| Area | Technologies | Status |
|---|---|---|
| Backend | pytest, pytest-asyncio, httpx | MVP / Core |
| Frontend | Vitest, React Testing Library | MVP / Core |
| API Testing | Postman or Bruno | MVP / Core |

## 15. Monitoring and Logging

| Technology / Approach | Purpose | Status |
|---|---|---|
| Python Logging | Basic application logging. | MVP / Core |
| Structured Logs | Consistent, structured log records. | MVP / Core |
| Application Error Logging | Record application errors. | MVP / Core |
| Prometheus | Production monitoring. | Future |
| Grafana | Production monitoring visualization. | Future |

## 16. MVP vs Future Technology Matrix

| Technology | Purpose | MVP | Phase 2 | Future Production |
|---|---|---|---|---|
| React, TypeScript, Vite | Frontend application | Yes | No | Yes |
| Tailwind CSS, shadcn/ui, Lucide React | Frontend styling and components | Yes | No | Yes |
| React Router, Axios, Recharts | Frontend routing, API communication, and visualization | Yes | No | Yes |
| FastAPI WebSockets | Real-time application updates | Yes | No | Yes |
| Python, FastAPI, Uvicorn, Pydantic | Backend APIs and orchestration | Yes | No | Yes |
| SQLAlchemy, Alembic | Database access and migrations | Yes | No | Yes |
| PyTorch and audio-processing libraries | Voice analysis and ML pipeline | Yes | No | Yes |
| Pretrained voice anti-spoofing model | Synthetic voice detection | Yes | No | Yes |
| LangChain, LangGraph, LLM API, Pydantic Structured Output | Advisory Security Copilot | Where feasible | No | Yes |
| Python rule-based risk engine | Deterministic risk scoring and policy validation | Yes | No | Yes |
| PostgreSQL | Persistent application data | Yes | No | Yes |
| Redis | Cache and real-time state | No | Optional | Yes |
| WebRTC | Browser audio streaming and low-latency communication | No | No | Yes |
| JWT, RBAC, Argon2, TLS, rate limiting, validation, audit logging | Application security | Yes | No | Yes |
| REST API | Core application integration | Yes | No | Yes |
| gRPC, webhooks, SDKs | Enterprise integration | No | No | Yes |
| Docker, Docker Compose | MVP deployment | Yes | No | Yes |
| Nginx | Production deployment | No | No | Yes |
| Kubernetes | Orchestration and horizontal scaling | No | No | Yes |
| pytest, pytest-asyncio, httpx | Backend testing | Yes | No | Yes |
| Vitest, React Testing Library | Frontend testing | Yes | No | Yes |
| Postman or Bruno | API testing | Yes | No | Yes |
| Python logging and structured logs | MVP observability | Yes | No | Yes |
| Prometheus, Grafana | Production monitoring | No | No | Yes |
