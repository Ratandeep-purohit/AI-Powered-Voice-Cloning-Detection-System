# System Architecture

## 1. Architecture Overview

The system is a modular, AI-powered cybersecurity platform for real-time or near-real-time detection of AI-generated, synthetic, or cloned voices. For the Smart India Hackathon MVP, it is implemented as a modular backend application rather than as separate microservices. This keeps development focused while retaining clear boundaries for future service extraction.

The React and TypeScript frontend communicates with the FastAPI backend through REST APIs for request-response operations and WebSockets for server-pushed, real-time updates. The backend orchestrates audio processing, ML detection, risk scoring, policy evaluation, alerting, and audit logging. PostgreSQL persists system data. LangGraph and the LLM support advisory reasoning and analyst assistance only; critical security actions remain deterministic and are controlled by backend policy rules.

## 2. Architecture Goals

- Provide near real-time voice analysis and risk updates.
- Maintain a modular design suitable for an MVP and future service extraction.
- Integrate security controls into application architecture.
- Support low-latency audio processing and risk scoring.
- Produce explainable risk assessments through detection signals and contextual factors.
- Minimize unnecessary raw-audio retention and support privacy-aware processing.
- Prioritize fast, reliable MVP implementation.
- Enable future horizontal scaling without introducing unnecessary initial complexity.

## 3. High-Level System Architecture

```mermaid
flowchart TD
    analyst[User / Security Analyst] --> frontend[React Frontend]
    frontend -->|REST API| api[FastAPI Backend]
    frontend <-->|WebSocket| ws[WebSocket Manager]
    ws --- api
    api --> audio[Audio Processing Module]
    audio --> ml[ML Voice Detection Module]
    ml --> risk[Risk Scoring Engine]
    risk --> policy[Policy Engine]
    policy --> alert[Alert Engine]
    alert --> frontend
    api --> copilot[Security Copilot]
    copilot -->|Advisory output| frontend
    api <--> db[(PostgreSQL Database)]
    risk <--> db
    alert <--> db
```

## 4. End-to-End System Flow

1. Audio is received from an MVP-supported input source.
2. The Audio Ingestion Module segments audio into processing chunks.
3. Voice activity detection identifies relevant speech.
4. The audio is normalized and prepared for analysis.
5. Features are extracted.
6. The pretrained anti-spoofing model analyzes the audio.
7. The model produces a synthetic voice probability.
8. The Risk Engine calculates a risk score.
9. Contextual information is incorporated into the score.
10. The Policy Engine evaluates deterministic rules.
11. Alerts or recommended actions are generated.
12. Real-time updates are sent through WebSockets.
13. Events and results are stored in PostgreSQL.
14. The Security Copilot may generate an explanation or incident summary for an analyst.

```mermaid
flowchart TD
    input[Audio received] --> chunks[Audio chunking]
    chunks --> vad[Voice activity detection]
    vad --> prepare[Noise handling and normalization]
    prepare --> features[Feature extraction]
    features --> model[Pretrained anti-spoofing model]
    model --> probability[Synthetic voice probability]
    probability --> scoring[Risk scoring with contextual information]
    scoring --> policy[Deterministic policy evaluation]
    policy --> action[Alert or recommended action]
    action --> updates[WebSocket updates]
    scoring --> db[(PostgreSQL)]
    action --> db
    scoring --> copilot[Advisory Security Copilot]
    copilot --> summary[Explanation or incident summary]
```

## 5. Frontend Architecture

The frontend is built with React, TypeScript, and Vite. Tailwind CSS and shadcn/ui support interface styling and reusable components; Lucide React provides icons. React Router manages navigation, Axios supports REST communication, Recharts supports visualization, and the WebSocket client receives live system events.

Major frontend modules are:

- Authentication
- Dashboard
- Live Call Monitoring
- Call Analysis View
- Alert Management
- Incident Investigation
- Security Copilot
- Administration
- Reports

```mermaid
flowchart TD
    user[User] --> app[React Application]
    app --> pages[Pages]
    pages --> components[Dashboard and feature components]
    components --> clients[Axios API Client / WebSocket Client]
    clients --> backend[FastAPI Backend]
```

## 6. Backend Architecture

The MVP uses a modular FastAPI backend. Modules operate within one application, and their interfaces provide boundaries for later extraction into independent services if required.

- **API Layer:** Receives REST and WebSocket requests and returns application responses.
- **Authentication Module:** Authenticates users and applies authorization checks.
- **Audio Ingestion Module:** Accepts and segments supported audio input.
- **Audio Processing Module:** Performs VAD, noise handling, normalization, and feature preparation.
- **Voice Detection Module:** Invokes the model-agnostic pretrained anti-spoofing detector.
- **Risk Scoring Engine:** Produces a weighted, contextual risk score independently of the LLM.
- **Policy Engine:** Applies deterministic policy and rule validation.
- **Alert Engine:** Creates alerts and recommended workflow actions.
- **Security Copilot Module:** Produces advisory explanations and structured recommendations.
- **WebSocket Manager:** Publishes live analysis, risk, and alert updates.
- **Database Layer:** Accesses PostgreSQL through SQLAlchemy and manages migrations through Alembic.
- **Audit Logging Module:** Captures relevant alerts, overrides, and configuration changes.

```mermaid
flowchart LR
    api[API Layer] --> auth[Authentication Module]
    api --> ingest[Audio Ingestion Module]
    ingest --> process[Audio Processing Module]
    process --> detect[Voice Detection Module]
    detect --> risk[Risk Scoring Engine]
    risk --> policy[Policy Engine]
    policy --> alerts[Alert Engine]
    alerts --> ws[WebSocket Manager]
    api --> copilot[Security Copilot Module]
    api --> data[Database Layer]
    risk --> data
    alerts --> data
    audit[Audit Logging Module] --> data
    policy --> audit
    alerts --> audit
```

## 7. Audio Processing Architecture

The MVP may accept microphone input, uploaded audio files, and simulated or streamed audio input. The pipeline remains compatible with future live telephony and VoIP integrations through SIP/RTP or platform-specific APIs.

Raw audio retention should be minimized where possible. Where required by privacy-sensitive deployments, the system can support feature-only logging and on-device or edge inference as described in the SRS.

```mermaid
flowchart TD
    input[Microphone, uploaded file, or simulated/streamed input] --> chunk[Audio chunking]
    chunk --> vad[Voice activity detection]
    vad --> noise[Noise handling]
    noise --> normalize[Audio normalization]
    normalize --> prepare[Feature preparation]
    prepare --> detect[ML detection]
```

## 8. Machine Learning Detection Pipeline

The ML pipeline uses PyTorch with torchaudio, librosa, NumPy, SciPy, PyDub, and WebRTC VAD. It uses a pretrained voice anti-spoofing or synthetic voice detection model. The detection layer is model-agnostic: a specific pretrained architecture is not assumed, allowing later replacement without changing the core system flow.

```mermaid
flowchart TD
    segment[Audio segment] --> extraction[Feature extraction]
    extraction --> representation[Spectral / acoustic representation]
    representation --> model[Pretrained voice anti-spoofing model]
    model --> classification[Model classification]
    classification --> probability[Synthetic voice probability]
    probability --> risk[Risk Scoring Engine]
```

## 9. Risk Scoring Architecture

The custom risk scoring system is implemented in Python and is independent of the LLM. It combines detection output with weighted contextual factors to produce a score from 0–100 and a classification of `SAFE`, `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.

Potential inputs are:

- Synthetic voice probability.
- Audio quality indicators.
- Voice consistency indicators.
- Caller information and reputation.
- Transaction context.
- Historical risk indicators.

```mermaid
flowchart TD
    ml[ML output] --> calculation[Weighted risk calculation]
    context[Contextual inputs] --> calculation
    calculation --> score[Risk score: 0–100]
    score --> classification[Risk classification]
    classification --> policy[Policy Engine]
```

## 10. Policy and Security Decision Architecture

The Policy Engine evaluates deterministic rules after risk assessment. It controls the security response and ensures that an LLM cannot bypass or replace policy enforcement.

Possible outputs are:

- No Action
- Warning
- Require Secondary Verification
- Escalate to Security Analyst
- Hold High-Risk Action

```mermaid
flowchart TD
    score[Risk score] --> policy[Policy Engine]
    policy --> rules[Rule evaluation]
    rules --> decision[Authorized decision]
    decision --> noaction[No action]
    decision --> warning[Warning]
    decision --> verification[Require secondary verification]
    decision --> escalate[Escalate to security analyst]
    decision --> hold[Hold high-risk action]
```

## 11. AI Security Copilot Architecture

The Security Copilot is an advisory component implemented with LangChain, LangGraph, an LLM API, and Pydantic Structured Output. It may explain why a call was flagged, summarize incidents, analyze available context, recommend verification steps, and assist analyst investigations through natural-language queries.

Its recommendation does not directly trigger critical actions. Such actions remain subject to deterministic policy and rule validation.

```mermaid
flowchart TD
    detection[Detection data] --> workflow[LangGraph workflow]
    score[Risk score] --> workflow
    context[Contextual information] --> workflow
    workflow --> reasoning[LLM reasoning]
    reasoning --> recommendation[Structured recommendation]
    recommendation --> analyst[Security Analyst]
```

## 12. Real-Time Communication Architecture

REST APIs support request-response operations. WebSockets support server-pushed live analysis progress, synthetic probability updates, risk score updates, alert notifications, and call-monitoring updates.

```mermaid
flowchart LR
    event[Backend event] --> manager[WebSocket Manager]
    manager --> connection[WebSocket connection]
    connection --> frontend[React Frontend]
    frontend --> dashboard[Dashboard component]
```

## 13. Database Architecture

PostgreSQL is the primary persistent database. Detailed schema design belongs in `docs/DATABASE.md`; this architecture identifies the logical data areas only.

- Users
- Organizations
- Calls
- Audio Segments
- Voice Analysis
- Risk Scores
- Alerts
- Alert Actions
- Audit Logs

```mermaid
flowchart TD
    organizations[Organizations] --> users[Users]
    organizations --> calls[Calls]
    calls --> segments[Audio Segments]
    segments --> analyses[Voice Analysis]
    analyses --> scores[Risk Scores]
    scores --> alerts[Alerts]
    alerts --> actions[Alert Actions]
    users --> audit[Audit Logs]
    alerts --> audit
```

## 14. Data Flow Architecture

Audio and active processing results are transient data. Persistent data includes authorized application records, analysis results, risk scores, alerts, alert actions, and audit logs. Raw audio retention is minimized where possible.

```mermaid
flowchart TD
    audio[Audio input] --> processing[Backend processing]
    processing --> ml[ML detection]
    ml --> risk[Risk Engine]
    risk --> policy[Policy Engine]
    policy --> alerts[Alerts]
    risk --> db[(Database)]
    alerts --> db
    alerts --> frontend[Frontend]
    db --> context[Security Copilot context]
    context --> copilot[Security Copilot recommendation]
    copilot --> frontend
```

## 15. API and Communication Architecture

### REST APIs

REST APIs are used for authentication, dashboard data, historical call data, alerts, reports, administration, and Security Copilot requests.

### WebSockets

WebSockets are used for live call analysis, real-time risk updates, and real-time alerts.

Detailed endpoint definitions belong in `docs/API.md`.

```mermaid
flowchart LR
    frontend[React Frontend] -->|REST requests| api[FastAPI REST API]
    api --> backend[Backend modules]
    backend --> db[(PostgreSQL)]
    backend --> ws[WebSocket Manager]
    ws -->|Live events| frontend
```

## 16. Security Architecture

The architecture applies JWT authentication, RBAC, Argon2 password hashing, input validation, API rate limiting, environment-based secrets, HTTPS/TLS, authorization checks, and audit logging. Detailed security controls belong in `docs/SECURITY.md`.

```mermaid
flowchart TD
    user[User] --> authentication[Authentication]
    authentication --> authorization[Authorization and RBAC]
    authorization --> api[Protected API]
    api --> modules[Business modules]
    modules --> db[(PostgreSQL)]
    authentication --> audit[Audit logging]
    authorization --> audit
    api --> audit
    modules --> audit
```

## 17. Docker Deployment Architecture

The MVP deployment uses Docker and Docker Compose. The core containers are `frontend`, `backend`, and `postgres`. Redis is optional and may be added later. The ML pipeline initially runs inside the backend container.

```mermaid
flowchart TD
    browser[Browser] --> frontend[Frontend container]
    frontend --> backend[Backend container: FastAPI and ML pipeline]
    backend --> postgres[(PostgreSQL container)]
    backend -. Optional .-> redis[(Redis container)]
```

## 18. Future Scalable Architecture

**Future Production Architecture — Not Required for Hackathon MVP**

The modular MVP can evolve into independently deployable services when justified by traffic, integration, or operational needs. Potential future infrastructure includes an API gateway, Redis, a message queue, Kubernetes, gRPC, webhooks, and SDKs. These technologies are future scope and are not implied to be part of the MVP.

```mermaid
flowchart TD
    gateway[API Gateway] --> auth[Authentication Service]
    gateway --> audio[Audio Processing Service]
    audio --> ml[ML Inference Service]
    ml --> risk[Risk Engine Service]
    risk --> alert[Alert Service]
    gateway --> copilot[Security Copilot Service]
    audio <--> queue[Message Queue]
    risk <--> redis[(Redis)]
    gateway --> webhooks[Webhooks / SDKs / gRPC]
    services[Services] --- kubernetes[Kubernetes]
```

## 19. Module Interaction Summary

| Module | Responsibility | Primary Inputs | Primary Outputs |
|---|---|---|---|
| Frontend | Present dashboard and user interfaces. | User interactions, REST responses, WebSocket events. | API requests, interface updates. |
| API Layer | Expose REST and WebSocket application interfaces. | Client requests. | Validated requests and responses. |
| Audio Processing | Prepare audio for detection. | Audio input. | Prepared audio features. |
| Voice Detection | Detect synthetic or cloned voice indicators. | Prepared audio features. | Synthetic voice probability. |
| Risk Engine | Calculate contextual risk. | Detection output and contextual factors. | Risk score and level. |
| Policy Engine | Apply deterministic security rules. | Risk score and policy configuration. | Authorized decision. |
| Alert Engine | Create alerts and recommended actions. | Policy decision. | Alerts and workflow actions. |
| Security Copilot | Provide analyst assistance. | Detection data, risk score, context. | Structured advisory recommendation. |
| WebSocket Manager | Publish real-time events. | Analysis, risk, and alert events. | Dashboard updates. |
| Database Layer | Persist and retrieve system data. | Module data operations. | Persistent data access. |
| Audit Logging | Record security-relevant activity. | Alerts, overrides, and configuration changes. | Audit records. |

## 20. Architecture Decisions

### Modular Monolith for MVP

The MVP avoids unnecessary microservices to reduce delivery and operational complexity. Module boundaries preserve a practical path to later extraction.

### Python-First ML Integration

FastAPI and PyTorch permit backend orchestration and ML integration in the same primary language and application context.

### Deterministic Security Actions

The LLM is advisory only. Critical actions must be evaluated through deterministic backend policy and rule validation to maintain controlled, auditable decisions.

### WebSockets for Real-Time Updates

WebSockets provide server-pushed updates needed for live analysis, risk scores, and alerts without repeated client polling.

### Model-Agnostic Detection Layer

The detection module accepts a pretrained anti-spoofing model without fixing a specific model architecture. This preserves the ability to replace or improve the detector without changing the core application design.

### PostgreSQL for Persistent Data

PostgreSQL is the primary persistent store for the application’s users, organizations, calls, analyses, scores, alerts, actions, and audit logs.

### Future Service Extraction

Audio processing, ML inference, risk scoring, alerting, authentication, and Security Copilot modules can be extracted as independent services later while preserving the system’s core flow.

## 21. Architecture Summary

The project uses a modular MVP architecture centered on a FastAPI backend, React and TypeScript frontend, PostgreSQL persistence, PyTorch-based model-agnostic voice detection, and WebSocket real-time updates. Audio analysis produces synthetic voice probability, which feeds an independent deterministic risk and policy engine. The Security Copilot provides advisory assistance only and cannot execute critical actions. Docker and Docker Compose provide the initial deployment model, while modular boundaries support a future scalability path when required.
