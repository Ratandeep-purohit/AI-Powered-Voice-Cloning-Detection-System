# Phase 11 — Dashboard Frontend

## 📋 Phase Information

| Category | Details |
|---|---|
| **Project** | AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks |
| **Phase Number** | 11 |
| **Phase Name** | Dashboard Frontend |
| **Module** | Security Monitoring & Operations Dashboard |
| **Status** | 🟡 Planned |
| **Dependencies** | Phase 00 — Foundation<br>Phase 01 — Database Core<br>Phase 02 — Authentication & Security<br>Phase 03 — Analysis Session<br>Phase 04 — Audio Processing Pipeline<br>Phase 05 — AI Detection Engine<br>Phase 06 — Risk Engine<br>Phase 07 — Policy & Prevention Engine<br>Phase 08 — Alerting & Monitoring<br>Phase 09 — Real-Time WebSocket<br>Phase 10 — Security Copilot |
| **Implementation Status** | Not Started |
| **Primary Output** | Complete Security Monitoring Dashboard |
| **Next Phase** | Phase 12 — Integration Testing |
| **Document Type** | Phase Implementation Specification |

---

# 1. Phase Objective

Phase 11 implements the complete frontend dashboard of the platform.

The dashboard acts as the primary operational interface for authorized users to:

- Monitor the overall security state.
- View analysis sessions.
- Inspect audio-processing status.
- Review AI detection results.
- Understand risk assessments.
- Investigate security alerts.
- Review prevention decisions and actions.
- Monitor real-time security events.
- Interact with Security Copilot.
- Navigate the complete security investigation workflow.

The frontend must consume and visualize the outputs produced by Phases 00–10.

The frontend must **not become the source of truth for security decisions**.

Backend systems remain authoritative for:

- Authentication.
- Authorization.
- Organization isolation.
- Analysis state.
- Audio processing.
- AI detection.
- Risk calculation.
- Policy evaluation.
- Prevention actions.
- Alert creation.
- Audit records.
- Security Copilot reasoning.

---

# 2. Phase Position in Overall Architecture

The complete platform flow entering Phase 11 is:

    User
      │
      ▼
    Authentication
      │
      ▼
    Analysis Session
      │
      ▼
    Audio Processing
      │
      ▼
    AI Detection
      │
      ▼
    Risk Engine
      │
      ▼
    Policy & Prevention
      │
      ├──────────────► Alerting & Monitoring
      │
      ├──────────────► Real-Time WebSocket
      │
      └──────────────► Security Copilot
                            │
                            ▼
                    ┌──────────────────┐
                    │ Dashboard        │
                    │ Frontend         │
                    └──────────────────┘
                            │
                            ▼
                         Operator

Phase 11 converts the backend security pipeline into a usable operator-facing interface.

---

# 3. Scope

## 3.1 Included

Phase 11 includes:

- Frontend application shell.
- Authentication-aware application loading.
- Protected frontend routes.
- Dashboard overview.
- Sidebar navigation.
- Header.
- Organization context display.
- Analysis session interface.
- Detection result interface.
- Risk assessment interface.
- Alert center.
- Alert details.
- Prevention history.
- Real-time activity feed.
- WebSocket UI integration.
- Security Copilot interface.
- API integration.
- Server-state handling.
- UI-state handling.
- Loading states.
- Empty states.
- Error states.
- Partial-failure handling.
- Responsive layouts.
- Accessibility.
- Security-safe rendering.
- Frontend testing.
- Reusable UI components.

---

# 4. Out of Scope

The following must not be newly implemented as frontend business logic in Phase 11:

- AI model training.
- AI inference implementation.
- Audio processing.
- Audio feature extraction.
- Risk calculation.
- Policy calculation.
- Prevention decision logic.
- Alert generation logic.
- Authentication backend.
- Authorization backend.
- Database redesign.
- WebSocket backend.
- Security Copilot intelligence.
- Backend tenant isolation.

The frontend only consumes these systems through their documented interfaces.

---

# 5. Frontend Technology

The frontend must continue using the foundation established in Phase 00.

| Layer | Technology |
|---|---|
| UI Framework | React |
| Language | TypeScript |
| Build Tool | Vite |
| API Communication | Project API client |
| Real-Time Communication | WebSocket |
| Routing | Existing React routing solution |
| Charts | Project-approved charting solution |
| Styling | Existing frontend styling architecture |
| Testing | Existing frontend testing framework |

Technology replacement should not be introduced during Phase 11 unless there is a documented architectural reason.

---

# 6. Frontend Architecture

The frontend architecture should follow a clear separation of responsibilities.

    ┌─────────────────────────────┐
    │           User              │
    └──────────────┬──────────────┘
                   │
                   ▼
    ┌─────────────────────────────┐
    │       React Application     │
    └──────────────┬──────────────┘
                   │
          ┌────────┼─────────┐
          │        │         │
          ▼        ▼         ▼
       Router    State    WebSocket
          │        │         │
          └────────┼─────────┘
                   │
                   ▼
          ┌─────────────────┐
          │   API Services  │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │    FastAPI      │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Backend Services│
          └────────┬────────┘
                   │
                   ▼
             PostgreSQL

The frontend must never directly communicate with PostgreSQL.

---

# 7. Recommended Frontend Structure

    frontend/
    │
    ├── src/
    │   │
    │   ├── app/
    │   │   ├── router/
    │   │   ├── providers/
    │   │   └── app.tsx
    │   │
    │   ├── components/
    │   │   ├── layout/
    │   │   ├── navigation/
    │   │   ├── cards/
    │   │   ├── charts/
    │   │   ├── tables/
    │   │   ├── alerts/
    │   │   ├── analysis/
    │   │   ├── detection/
    │   │   ├── risk/
    │   │   ├── prevention/
    │   │   └── copilot/
    │   │
    │   ├── pages/
    │   │   ├── dashboard/
    │   │   ├── analysis/
    │   │   ├── detection/
    │   │   ├── risk/
    │   │   ├── alerts/
    │   │   ├── prevention/
    │   │   ├── copilot/
    │   │   └── settings/
    │   │
    │   ├── services/
    │   │   ├── api/
    │   │   └── websocket/
    │   │
    │   ├── hooks/
    │   ├── stores/
    │   ├── types/
    │   ├── utils/
    │   └── styles/
    │
    ├── tests/
    │
    └── package.json

The exact structure may differ if an existing implementation already follows another organization pattern.

The important requirement is separation of:

- Pages.
- Reusable components.
- API services.
- WebSocket services.
- State.
- Types.
- Utilities.

---

# 8. Application Layout

The main application should follow a security-SaaS dashboard structure.

    ┌──────────────────────────────────────────────────────────┐
    │ Header                                                   │
    │ Page Title                     Connection   User Menu    │
    ├─────────────────┬────────────────────────────────────────┤
    │                 │                                        │
    │ Sidebar         │              Main Content              │
    │                 │                                        │
    │ Dashboard       │                                        │
    │ Analysis        │                                        │
    │ Detection       │                                        │
    │ Risk            │                                        │
    │ Alerts          │                                        │
    │ Prevention      │                                        │
    │ Copilot         │                                        │
    │                 │                                        │
    │ Settings        │                                        │
    │                 │                                        │
    └─────────────────┴────────────────────────────────────────┘

The layout must support:

- Desktop.
- Laptop.
- Tablet.
- Mobile.
- Collapsible navigation.
- Active navigation state.
- Role-aware UI.
- Responsive content.
- Global status indicators.

---

# 9. Navigation

Primary navigation:

    Dashboard
        │
        ├── Overview
        │
        ├── Analysis
        │
        ├── Detection
        │
        ├── Risk
        │
        ├── Alerts
        │
        ├── Prevention
        │
        ├── Security Copilot
        │
        └── Settings

Navigation visibility may be role-aware.

However:

    Frontend Permission
          ≠
    Backend Authorization

Hiding a UI element does not provide security.

Every protected operation must still be authorized by the backend.

---

# 10. Dashboard Overview

The dashboard is the main operational page.

It should provide a concise overview of the organization's current security state.

Recommended sections:

    Security Status
          │
          ├── Key Metrics
          │
          ├── Risk Distribution
          │
          ├── Detection Summary
          │
          ├── Recent Alerts
          │
          ├── Recent Analyses
          │
          └── Live Activity

---

# 11. Dashboard Wireframe

    ┌────────────────────────────────────────────────────────────┐
    │ Security Overview                                          │
    │ Current organization security state                        │
    ├──────────────┬──────────────┬──────────────┬────────────── ┤
    │ Total        │ High Risk    │ Open Alerts  │ Critical      │
    │ Analyses     │ Analyses     │              │ Alerts        │
    │              │              │              │               │ 
    ├──────────────┴──────────────┴──────────────┴────────────── ┤
    │                                                            │
    │                  Risk Distribution                         │
    │                                                            │
    ├────────────────────────────────────┬───────────────────────┤
    │ Recent Alerts                      │ Live Activity         │
    │                                    │                       │
    │ Critical alert                     │ Analysis started      │
    │ High-risk alert                    │ Detection completed   │
    │ Medium alert                       │ Risk updated          │
    │                                    │ Alert created         │
    └────────────────────────────────────┴───────────────────────┘

The overview must prioritize security information rather than decorative elements.

---

# 12. Security Metrics

Metrics must come from backend data.

Potential metrics include:

| Metric | Meaning |
|---|---|
| Total Analyses | Total analysis sessions visible to the user |
| Processing | Currently processing analyses |
| Completed | Successfully completed analyses |
| Failed | Failed analyses |
| High Risk | High-risk analysis count |
| Critical Alerts | Critical alerts |
| Open Alerts | Currently open alerts |
| Resolved Alerts | Resolved alerts |
| Prevention Events | Recorded prevention events |
| Detection Distribution | Detection classification distribution |

The frontend must never invent security metrics.

Data flow:

    Backend
       ↓
    API Response
       ↓
    Response Validation
       ↓
    Frontend State
       ↓
    Dashboard Component
       ↓
    UI

---

# 13. Security Status

The dashboard should provide an overall status area.

Possible states:

- Normal.
- Attention Required.
- Elevated Risk.
- Critical.

The exact status must be derived from backend-defined security data or documented rules.

The frontend must not independently invent security conclusions.

---

# 14. Analysis Session Interface

The Analysis page provides access to analysis sessions.

Recommended fields:

| Field | Description |
|---|---|
| Session ID | Unique analysis identifier |
| Status | Current analysis status |
| Created At | Creation timestamp |
| Duration | Processing duration |
| Detection | Detection state/result |
| Risk | Risk level |
| Alert | Related alert state |
| Actions | Authorized operations |

Example:

    ┌───────────────────────────────────────────────────────────┐
    │ Analysis Sessions                                         │
    ├────────────┬────────────┬──────────┬─────────┬────────────┤
    │ Session ID │ Status     │ Detection│ Risk    │ Created    │
    ├────────────┼────────────┼──────────┼─────────┼────────────┤
    │ A-10291    │ Completed  │ Suspicious│ High   │ 12:40      │
    │ A-10290    │ Processing │ Pending  │ Pending │ 12:38      │
    │ A-10289    │ Completed  │ Normal   │ Low     │ 12:32      │
    └────────────┴────────────┴──────────┴─────────┴────────────┘

Exact fields must follow the backend API contract.

---

# 15. Analysis Detail Page

The analysis detail page should provide a complete view of a single analysis.

    Analysis Session
          │
          ├── Session Information
          │
          ├── Audio Information
          │
          ├── Processing Status
          │
          ├── Detection Result
          │
          ├── Risk Assessment
          │
          ├── Alerts
          │
          ├── Prevention Actions
          │
          └── Timeline

The user should be able to move from an analysis to all related security information without losing context.

---

# 16. Analysis Timeline

A chronological timeline should show important events.

Example:

    12:40:01
    Analysis Created
          ↓
    12:40:02
    Audio Processing Started
          ↓
    12:40:04
    Audio Processing Completed
          ↓
    12:40:06
    AI Detection Completed
          ↓
    12:40:07
    Risk Assessment Generated
          ↓
    12:40:08
    Alert Created
          ↓
    12:40:09
    Policy Evaluated

The timeline must use actual backend timestamps.

---

# 17. Detection Results Interface

The Detection page must present AI detection results in an understandable way.

Recommended information:

- Detection classification.
- Confidence.
- Detection signals.
- Evidence references.
- Model information where available.
- Analysis association.
- Timestamp.
- Explanation where provided by the backend.

Example:

    ┌─────────────────────────────────────────┐
    │ Detection Result                        │
    ├─────────────────────────────────────────┤
    │ Classification                          │
    │                                         │
    │ HIGH RISK                               │
    │                                         │
    │ Confidence                              │
    │                                         │
    │ 94%                                     │
    ├─────────────────────────────────────────┤
    │ Detection Signals                       │
    │                                         │
    │ Signal A        ██████████              │
    │ Signal B        ████████                │
    │ Signal C        ██████                  │
    ├─────────────────────────────────────────┤
    │ Explanation                             │
    │                                         │
    │ Detection engine identified signals     │
    │ associated with synthetic speech.       │
    └─────────────────────────────────────────┘

Confidence must not be presented as absolute certainty.

Avoid language such as:

    "100% fake"
    "Guaranteed cloned voice"

unless such semantics are explicitly defined by the backend contract.

---

# 18. Detection Evidence

When evidence is available, the frontend should show it clearly.

Evidence may include:

- Detection signal.
- Feature.
- Model output.
- Timestamp.
- Related analysis.
- Backend evidence reference.

The frontend must not fabricate evidence.

---

# 19. Risk Assessment Interface

The Risk page should provide a clear representation of the backend-generated risk assessment.

Recommended information:

- Risk score.
- Risk level.
- Contributing factors.
- Detection association.
- Analysis association.
- Timestamp.
- Historical risk where available.

Example:

    ┌─────────────────────────────────────────┐
    │ Risk Assessment                         │
    ├─────────────────────────────────────────┤
    │ Risk Level                              │
    │                                         │
    │ HIGH                                    │
    │                                         │
    │ Risk Score                              │
    │                                         │
    │ 87 / 100                                │
    ├─────────────────────────────────────────┤
    │ Contributing Factors                    │
    │                                         │
    │ Detection confidence       +35          │
    │ Synthetic indicators       +25          │
    │ Behavioral signals         +17          │
    │ Policy factors             +10          │
    │                                         │
    │ Total                       87          │
    └─────────────────────────────────────────┘

The frontend must display the backend result.

It must not independently recalculate risk.

---

# 20. Risk Visualization

Potential visualizations:

- Risk score indicator.
- Risk distribution.
- Risk trend.
- Risk factor list.
- Risk timeline.

Example:

    Risk Distribution

    Critical   █████
    High       ███████████
    Medium     ███████████████
    Low        ███████████████████

Charts should always provide an accessible textual representation.

---

# 21. Severity System

Severity must remain consistent across the entire dashboard.

| Severity | Meaning |
|---|---|
| Informational | Informational security event |
| Low | Low-level concern |
| Medium | Investigation may be required |
| High | Significant concern |
| Critical | Immediate attention required |

Severity must not rely exclusively on color.

Use:

- Text.
- Iconography.
- Visual state.
- Accessible labels.

---

# 22. Alert Center

The Alert Center is the main location for security alert investigation.

Recommended structure:

    ┌───────────────────────────────────────────────────────────┐
    │ Alerts                                                    │
    ├──────────┬──────────┬────────────┬──────────┬─────────────┤
    │ Severity │ Status   │ Created    │ Analysis │ Action      │
    ├──────────┼──────────┼────────────┼──────────┼─────────────┤
    │ Critical │ Open     │ 12:40      │ A-1293   │ Investigate │
    │ High     │ Open     │ 12:37      │ A-1290   │ Review      │
    │ Medium   │ Resolved │ 11:51      │ A-1278   │ View        │
    └──────────┴──────────┴────────────┴──────────┴─────────────┘

---

# 23. Alert Filtering

Where supported by the backend API, filters should include:

- Severity.
- Status.
- Date/time.
- Risk level.
- Analysis.
- Detection classification.

Example:

    Severity: [All]
    Status:   [Open]
    Risk:     [High]
    Date:     [Last 24 hours]

Filtering must use documented backend capabilities.

Large datasets should use server-side filtering rather than loading the complete dataset into the browser.

---

# 24. Alert Detail

Alert details should include:

    Alert
      │
      ├── Alert ID
      ├── Severity
      ├── Status
      ├── Trigger
      ├── Created At
      ├── Related Analysis
      ├── Detection Evidence
      ├── Risk Assessment
      ├── Prevention Decision
      ├── Timeline
      └── Authorized Actions

The UI should clearly show relationships between:

    Analysis
        ↓
    Detection
        ↓
    Risk
        ↓
    Alert
        ↓
    Prevention

---

# 25. Prevention Interface

The Prevention page displays policy and response outcomes.

Recommended information:

- Policy.
- Trigger.
- Decision.
- Action.
- Status.
- Timestamp.
- Related alert.
- Related analysis.
- Operator action.
- System action.

Example:

    ┌─────────────────────────────────────────┐
    │ Prevention Event                        │
    ├─────────────────────────────────────────┤
    │ Policy                                  │
    │ High-Risk Voice Detection               │
    │                                         │
    │ Decision                                │
    │ REVIEW_REQUIRED                         │
    │                                         │
    │ Related Alert                           │
    │ AL-1029                                 │
    │                                         │
    │ Status                                  │
    │ Completed                               │
    │                                         │
    │ Timestamp                               │
    │ 2026-09-03 12:40:21                     │
    └─────────────────────────────────────────┘

The UI must distinguish:

    Recommended Action
          ≠
    Executed Action

Only backend-confirmed actions may be displayed as executed.

---

# 26. Security Copilot Interface

The Security Copilot page provides an operator-facing AI assistance interface.

Recommended flow:

    User Question
          ↓
    Copilot Request
          ↓
    Backend Authorization
          ↓
    Context Retrieval
          ↓
    Copilot Processing
          ↓
    Structured Response
          ↓
    Dashboard

Example:

    ┌──────────────────────────────────────────────────────┐
    │ Security Copilot                                     │
    ├──────────────────────────────────────────────────────┤
    │                                                      │
    │ Ask about alerts, detection, risk or analysis.       │
    │                                                      │
    │ ┌──────────────────────────────────────────────────┐ │
    │ │ Why was this session marked high risk?           │ │
    │ └──────────────────────────────────────────────────┘ │
    │                                                      │
    │                  [ Ask Copilot ]                     │
    │                                                      │
    ├──────────────────────────────────────────────────────┤
    │ Response                                             │
    │                                                      │
    │ The analysis was classified as high risk based on    │  
    │ the available detection and risk assessment data.    │
    │                                                      │
    │ Evidence                                             │
    │ • Analysis                                           │
    │ • Detection result                                   │
    │ • Risk assessment                                    │
    │                                                      │
    │ Recommendations                                      │
    │ • Review the associated alert                        │
    │ • Verify the caller independently                    │
    └──────────────────────────────────────────────────────┘

The frontend must clearly distinguish:

    System Evidence
          ↓
    AI Explanation
          ↓
    Recommendation

---

# 27. Real-Time WebSocket Integration

Phase 11 consumes the real-time event system implemented in Phase 09.

Architecture:

    Backend
       │
       │ WebSocket Event
       ▼
    WebSocket Client
       │
       ▼
    Event Validation
       │
       ▼
    State Update
       │
       ▼
    UI Update

Real-time events may update:

- Dashboard metrics.
- Alert counters.
- Alert lists.
- Analysis status.
- Detection status.
- Risk status.
- Prevention events.
- Activity feed.

---

# 28. WebSocket Event Model

Supported event types must follow the Phase 09 contract.

Potential events include:

    ANALYSIS_STARTED
    ANALYSIS_COMPLETED
    ANALYSIS_FAILED
    DETECTION_COMPLETED
    RISK_UPDATED
    ALERT_CREATED
    ALERT_ESCALATED
    ALERT_RESOLVED
    PREVENTION_TRIGGERED
    PREVENTION_COMPLETED

The frontend must not assume undocumented event types.

Unknown event types must be ignored or handled safely.

Unknown events must not crash the application.

---

# 29. Real-Time Event Flow

    Security Event
          ↓
    WebSocket Server
          ↓
    Frontend WebSocket Client
          ↓
    Parse Event
          ↓
    Validate Event
          ↓
    Identify Event Type
          ↓
    Update Relevant State
          ↓
    Refresh Affected UI
          ↓
    Display Activity

The backend remains the source of truth.

---

# 30. WebSocket Connection State

The dashboard should display the current real-time connection state.

Possible states:

    Connected
    Connecting
    Reconnecting
    Disconnected

Example:

    ● Real-time Connected

or:

    Real-time connection unavailable.
    Trying to reconnect...

The UI must never claim that live monitoring is active when the WebSocket connection is unavailable.

---

# 31. WebSocket Reconnection

When disconnected:

    Connection Lost
          ↓
    Mark UI as Disconnected
          ↓
    Attempt Reconnection
          ↓
    Connection Restored
          ↓
    Refresh / Reconcile Relevant Data

The implementation must avoid creating uncontrolled reconnect loops.

Reconnection behavior must be compatible with the Phase 09 backend design.

---

# 32. Event Deduplication

The frontend should safely handle duplicate real-time events where event identifiers or backend semantics permit deduplication.

Possible strategy:

    Event ID
       ↓
    Already Processed?
       │
       ├── Yes → Ignore
       │
       └── No  → Process

The exact strategy must follow the WebSocket event contract.

---

# 33. API Service Architecture

API communication should be centralized.

Recommended structure:

    services/
    └── api/
        ├── auth.ts
        ├── dashboard.ts
        ├── analysis.ts
        ├── detection.ts
        ├── risk.ts
        ├── alerts.ts
        ├── prevention.ts
        └── copilot.ts

React components should not duplicate request logic.

---

# 34. API Request Flow

    React Component
          ↓
    API Service
          ↓
    HTTP Request
          ↓
    FastAPI
          ↓
    Authentication
          ↓
    Authorization
          ↓
    Application Service
          ↓
    Database
          ↓
    API Response
          ↓
    Frontend State
          ↓
    Component

---

# 35. API Response Handling

The frontend should handle:

- Successful response.
- Empty response.
- Validation failure.
- Authentication failure.
- Authorization failure.
- Not found.
- Conflict.
- Rate limit.
- Server error.
- Network failure.
- Timeout.

The UI must not expose raw backend exceptions.

---

# 36. HTTP Error Mapping

Recommended frontend handling:

    401
      ↓
    Authentication expired / invalid
      ↓
    Re-authentication flow

    403
      ↓
    Access denied

    404
      ↓
    Resource not found

    409
      ↓
    Conflict

    422
      ↓
    Invalid request

    429
      ↓
    Too many requests

    500+
      ↓
    Controlled server error

The exact behavior must follow the backend API contract.

---

# 37. Authentication State

The frontend must integrate with Phase 02 authentication.

Expected flow:

    Login
      ↓
    Authentication Success
      ↓
    Authenticated State
      ↓
    Dashboard

If authentication expires:

    API Authentication Failure
          ↓
    Clear Invalid Auth State
          ↓
    Redirect to Login / Re-authentication

The frontend must never expose:

- JWT signing secrets.
- Password hashes.
- Database credentials.
- Server secrets.
- Internal privileged tokens.

---

# 38. Protected Routes

Protected pages should include:

    /dashboard
    /analysis
    /analysis/:id
    /detection
    /detection/:id
    /risk
    /risk/:id
    /alerts
    /alerts/:id
    /prevention
    /copilot
    /settings

Exact route names may be adapted to the existing implementation.

Unauthenticated users must not be allowed to render protected application content.

---

# 39. Frontend Authorization UX

The frontend may use the authenticated user's role/permissions to:

- Hide unavailable navigation.
- Disable unavailable actions.
- Avoid unnecessary requests.
- Display appropriate UI.

However:

    Frontend authorization
            ↓
        UX control

    Backend authorization
            ↓
        Security boundary

Backend authorization must always be authoritative.

---

# 40. Organization Context

The dashboard must operate within the authenticated user's organization context.

The frontend must not permit arbitrary organization switching through unsafe client-side state.

Correct flow:

    Authenticated User
          ↓
    Authenticated Organization
          ↓
    Authorized API Requests
          ↓
    Organization Data

The client must not be able to override organization ownership merely by changing:

- URL parameters.
- Local storage values.
- Query parameters.
- Request body fields.

The backend must enforce tenant isolation.

---

# 41. State Management

Frontend state should be separated into logical categories.

    ┌──────────────────────────────┐
    │ Authentication State         │
    │ User / Organization          │
    └──────────────────────────────┘

    ┌──────────────────────────────┐
    │ Server State                 │
    │ API Data                     │
    └──────────────────────────────┘

    ┌──────────────────────────────┐
    │ Real-Time State              │
    │ WebSocket Events             │
    └──────────────────────────────┘

    ┌──────────────────────────────┐
    │ UI State                     │
    │ Filters / Modals / Sidebar   │
    └──────────────────────────────┘

Server state should not be unnecessarily duplicated across multiple stores.

---

# 42. Loading States

Every major data-dependent page must have a loading state.

Examples:

    Loading dashboard...

    Loading analysis sessions...

    Loading detection result...

    Loading risk assessment...

    Loading alerts...

    Loading prevention history...

    Loading Copilot...

For large visual sections, skeleton loaders may be used.

Loading states must not look like real security data.

---

# 43. Empty States

Empty state must be clearly different from errors.

Example:

    No alerts found.

    There are currently no alerts matching the selected filters.

Analysis:

    No analysis sessions available.

    Start an analysis to see results here.

The UI must not interpret absence of records as proof of security.

Avoid misleading messages such as:

    "Everything is safe."

unless the backend explicitly provides such a conclusion.

---

# 44. Error States

Error messages must be:

- Clear.
- Short.
- Actionable.
- Non-technical where possible.

Example:

    Unable to load security data.

    Please try again.

Possible action:

    [ Retry ]

Do not expose:

- Stack traces.
- SQL errors.
- Internal file paths.
- Internal service URLs.
- Credentials.
- Tokens.
- Infrastructure details.

---

# 45. Partial Failure Handling

A single failed widget should not necessarily break the entire dashboard.

Example:

    Dashboard

    Security Metrics       ✓ Available
    Risk Distribution      ✓ Available
    Recent Alerts          ✕ Failed
    Live Activity          ✓ Available

The failed section should display its own error state.

The remaining dashboard should continue functioning.

---

# 46. Data Refresh

The dashboard may combine:

- Initial API loading.
- Manual refresh.
- Background refresh.
- Real-time WebSocket updates.

The implementation must avoid unnecessary duplicate API requests.

When real-time events arrive, only affected data should be updated or revalidated where practical.

---

# 47. Search

Search should be provided where useful and supported.

Potential search targets:

- Analysis ID.
- Alert ID.
- Session ID.
- Relevant identifiers.

Search should be:

- Debounced where appropriate.
- Server-side for large datasets.
- Clearly cancellable/resettable.

---

# 48. Filtering

Common filters:

    Severity
    Status
    Risk
    Detection
    Date Range
    Analysis

Filter state should be predictable and easy to clear.

Example:

    [High] [Open] [Last 24h] [Clear Filters]

---

# 49. Pagination

Large datasets must not be loaded completely into the browser.

Preferred flow:

    Browser
       ↓
    Request Page 1
       ↓
    Backend
       ↓
    20 / configured records
       ↓
    Browser

Then:

    Next Page
       ↓
    Request Page 2

Pagination should follow backend API capabilities.

---

# 50. Table Design

Security tables should prioritize important information.

Recommended properties:

- Clear column headers.
- Sortable columns where supported.
- Pagination.
- Filtering.
- Row navigation.
- Status indicators.
- Responsive behavior.
- Keyboard accessibility.

Important information should remain visible on smaller screens.

---

# 51. Mobile and Responsive Design

The application must support:

    Desktop
    Laptop
    Tablet
    Mobile

Desktop:

    Sidebar + Main Content

Tablet:

    Collapsible Sidebar
    +
    Responsive Content

Mobile:

    Navigation Drawer
    +
    Single Column Layout

Tables should support horizontal scrolling or alternate card/detail layouts where necessary.

---

# 52. Accessibility

The dashboard should implement:

- Semantic HTML.
- Keyboard navigation.
- Visible focus states.
- Accessible buttons.
- Proper labels.
- Accessible forms.
- Accessible dialogs.
- Accessible menus.
- Screen-reader-compatible status indicators.
- Sufficient contrast.
- Text-based severity labels.
- Accessible chart summaries.

Real-time updates must not unexpectedly steal keyboard focus.

---

# 53. Chart Requirements

Charts may be used for:

- Risk distribution.
- Detection distribution.
- Alert trend.
- Analysis volume.
- Risk trend.

Each chart must have:

- Meaningful title.
- Relevant labels.
- Legend where needed.
- Accessible textual summary.
- Loading state.
- Empty state.
- Error state.

Charts must communicate information, not merely decorate the dashboard.

---

# 54. Notification System

The dashboard may display notifications for important security events.

Potential notifications:

- Critical alert created.
- High-risk detection completed.
- Alert escalated.
- Prevention triggered.
- Analysis completed.
- Real-time connection restored.
- Real-time connection lost.

Notifications should not unnecessarily expose sensitive information.

---

# 55. Activity Feed

The live activity feed should display recent system events.

Example:

    ● 12:41:03
      Critical alert created
      Analysis A-1293

    ● 12:40:58
      High-risk detection completed
      Confidence: 94%

    ● 12:40:51
      Analysis completed
      Session A-1293

The activity feed should use actual event data.

---

# 56. Audit Information

Where the backend exposes authorized audit information, the frontend may display it.

Example:

    12:40:01
    Alert Created

    12:40:12
    Operator Viewed Alert

    12:41:02
    Response Action Confirmed

The frontend must never fabricate audit records.

---

# 57. Security-Safe Rendering

All backend-provided content must be treated as untrusted input.

The frontend must safely render:

- User-provided text.
- Alert descriptions.
- Analysis metadata.
- Copilot responses.
- Evidence descriptions.
- Organization data.

Avoid unsafe HTML rendering unless absolutely required and properly sanitized.

---

# 58. XSS Protection

The frontend must protect against:

- Stored XSS.
- Reflected XSS.
- DOM-based XSS.

Do not directly inject untrusted content into HTML.

Especially protect:

- Copilot responses.
- Alert descriptions.
- User names.
- Organization names.
- Analysis metadata.
- Backend error messages.

---

# 59. Sensitive Data Protection

The browser must not expose:

- Database passwords.
- Environment variables containing secrets.
- JWT signing keys.
- API private keys.
- Internal service credentials.
- Password hashes.
- Administrative secrets.

Production frontend configuration must contain only values intended for client-side use.

---

# 60. Browser Logging

Production frontend logging must not expose sensitive information.

Avoid logging:

- Access tokens.
- Authentication payloads.
- Passwords.
- API secrets.
- Complete sensitive audio metadata.
- Private user information.
- Internal authorization details.

Debug logging should be appropriately disabled or controlled in production.

---

# 61. No Fabricated Security Data

The production dashboard must never fabricate:

- Alerts.
- Detection results.
- Risk scores.
- Analysis sessions.
- Prevention actions.
- Audit events.
- Security incidents.
- Copilot evidence.

Mock data is allowed only in:

- Unit tests.
- Integration tests.
- Local development.
- Explicit demo environments.

Production data must come from backend systems.

---

# 62. No Business Logic Duplication

The frontend must not independently implement:

- Detection algorithms.
- Risk scoring.
- Policy evaluation.
- Prevention logic.
- Alert creation.
- Tenant isolation.
- Backend authorization.

The frontend displays backend-owned decisions.

---

# 63. Error Recovery

The UI should provide recovery mechanisms where appropriate.

Examples:

    API Failure
       ↓
    Retry

    WebSocket Failure
       ↓
    Reconnect

    Missing Resource
       ↓
    Return to List

    Authentication Expired
       ↓
    Re-authenticate

Recovery actions must not cause duplicate destructive operations.

---

# 64. Frontend Route Model

Recommended route structure:

    /
      ↓
    /dashboard

    /analysis
      ↓
    /analysis/:id

    /detection
      ↓
    /detection/:id

    /risk
      ↓
    /risk/:id

    /alerts
      ↓
    /alerts/:id

    /prevention

    /copilot

    /settings

Routes must follow the project's existing routing architecture where already established.

---

# 65. Security Investigation Workflow

The frontend must support a coherent investigation path.

    Dashboard
       ↓
    Critical Alert
       ↓
    Alert Details
       ↓
    Related Analysis
       ↓
    Detection Result
       ↓
    Risk Assessment
       ↓
    Prevention Decision
       ↓
    Security Copilot
       ↓
    Recommended Next Step

The user should not lose the context of the original alert while navigating related records.

---

# 66. End-to-End UI Flow

    User Login
         ↓
    Authenticated Dashboard
         ↓
    Security Overview
         ↓
    Live Monitoring
         ↓
    Analysis Session
         ↓
    Detection Result
         ↓
    Risk Assessment
         ↓
    Alert Investigation
         ↓
    Prevention Decision
         ↓
    Security Copilot
         ↓
    Recommended Action

---

# 67. Real-Time Dashboard Sequence

    Security Event
          │
          ▼
    Backend Event Publisher
          │
          ▼
    WebSocket Server
          │
          ▼
    Frontend WebSocket Client
          │
          ▼
    Event Validation
          │
          ▼
    State Update
          │
          ▼
    Dashboard Components
          │
          ▼
    Operator

The dashboard must remain functional even if the real-time connection temporarily fails.

---

# 68. Dashboard Data Flow

    ┌─────────────────────────┐
    │       PostgreSQL        │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │    Backend Services     │
    └────────────┬────────────┘
                 │
          ┌──────┴──────┐
          │             │
          ▼             ▼
       REST API      WebSocket
          │             │
          └──────┬──────┘
                 ▼
    ┌─────────────────────────┐
    │     React Frontend      │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │      Security UI        │
    └─────────────────────────┘

---

# 69. Component Architecture

Recommended reusable components:

    Layout
    ├── AppLayout
    ├── Sidebar
    ├── Header
    ├── PageContainer
    └── MobileNavigation

    Dashboard
    ├── MetricCard
    ├── SecurityStatus
    ├── RiskDistribution
    ├── DetectionSummary
    ├── AlertSummary
    └── ActivityFeed

    Analysis
    ├── AnalysisTable
    ├── AnalysisStatus
    ├── AnalysisDetails
    └── AnalysisTimeline

    Detection
    ├── DetectionSummary
    ├── ConfidenceIndicator
    ├── DetectionSignalList
    └── DetectionDetails

    Risk
    ├── RiskCard
    ├── RiskScore
    ├── RiskFactors
    └── RiskTimeline

    Alerts
    ├── AlertTable
    ├── SeverityBadge
    ├── AlertFilters
    ├── AlertDetails
    └── AlertTimeline

    Prevention
    ├── PreventionTable
    ├── PreventionStatus
    ├── PolicyDecision
    └── ResponseTimeline

    Copilot
    ├── CopilotInput
    ├── CopilotMessage
    ├── EvidenceList
    └── RecommendationList

Components should remain focused and reusable.

---

# 70. UI State Model

Common UI states:

    INITIAL
       ↓
    LOADING
       ↓
    SUCCESS
       │
       ├── DATA
       │
       └── EMPTY

or:

    LOADING
       ↓
    ERROR
       ↓
    RETRY

Real-time state:

    CONNECTING
       ↓
    CONNECTED
       │
       ├── EVENT RECEIVED
       │
       └── EVENT PROCESSED
       │
       ▼
    DISCONNECTED
       ↓
    RECONNECTING
       ↓
    CONNECTED

---

# 71. Analysis State Visualization

The frontend may represent backend analysis states such as:

    CREATED
       ↓
    PROCESSING
       ↓
    DETECTION
       ↓
    RISK_ASSESSMENT
       ↓
    COMPLETED

Failure path:

    PROCESSING
       ↓
    FAILED

Exact status values must follow the backend contract.

The frontend must not invent incompatible state names.

---

# 72. Alert State Visualization

Possible lifecycle:

    CREATED
       ↓
    OPEN
       ↓
    ACKNOWLEDGED
       ↓
    RESOLVED

Exact states must follow the backend alert model.

The frontend must not assume a state transition occurred unless confirmed by the backend.

---

# 73. Data Formatting

The frontend should consistently format:

- Dates.
- Times.
- Durations.
- Risk scores.
- Confidence.
- IDs.
- Status.
- Severity.

Example:

    Backend:
    2026-09-03T12:40:21.293842Z

    UI:
    03 Sep 2026, 12:40:21 UTC

The underlying backend value must remain unchanged.

---

# 74. Long Data Handling

Long identifiers and strings should not break layouts.

Possible approaches:

- Truncation.
- Tooltip.
- Copy action.
- Detail page.

Example:

    9a9b0b6e-...-5b71

The full identifier must remain accessible where appropriate.

---

# 75. Performance Requirements

The dashboard should prioritize:

- Fast initial render.
- Efficient API usage.
- Efficient state updates.
- Minimal unnecessary re-renders.
- Pagination.
- Lazy loading where useful.
- Debounced search.
- Efficient WebSocket processing.
- Appropriate caching.

Do not introduce arbitrary performance numbers unless they are defined elsewhere in the project requirements.

Performance thresholds should be validated in Phase 12.

---

# 76. Frontend Testing Strategy

Phase 11 testing must cover:

    Components
       ↓
    Pages
       ↓
    Routing
       ↓
    Authentication
       ↓
    Authorization UX
       ↓
    API Integration
       ↓
    WebSocket Integration
       ↓
    Error Handling
       ↓
    Security
       ↓
    Responsive Behavior

---

# 77. Component Tests

Test:

- Metric cards.
- Status badges.
- Severity indicators.
- Risk indicators.
- Tables.
- Filters.
- Forms.
- Modals.
- Alert components.
- Analysis components.
- Detection components.
- Copilot components.
- Loading states.
- Empty states.
- Error states.

---

# 78. Page Tests

Test:

- Dashboard.
- Analysis list.
- Analysis detail.
- Detection list/detail.
- Risk list/detail.
- Alert list.
- Alert detail.
- Prevention page.
- Copilot page.
- Settings page where included.

---

# 79. Authentication Tests

Verify:

    Unauthenticated User
          ↓
    Login Page

    Authenticated User
          ↓
    Dashboard

    Expired Authentication
          ↓
    Re-authentication

Protected content must not remain accessible after authentication becomes invalid.

---

# 80. Authorization UX Tests

Verify:

- Authorized actions are visible.
- Restricted actions are hidden or disabled appropriately.
- Unauthorized backend responses are handled safely.
- Restricted pages do not render sensitive information.

Backend authorization must also be tested independently in the backend test suite.

---

# 81. Tenant Isolation Tests

Verify that the frontend:

- Uses the authenticated organization context.
- Does not allow unsafe organization overrides.
- Handles cross-organization authorization failures safely.
- Never renders data from unauthorized responses.

Tenant isolation itself remains a backend responsibility.

---

# 82. WebSocket Tests

Test:

- Initial connection.
- Connection success.
- Authentication behavior.
- Event parsing.
- Event validation.
- Known event types.
- Unknown event types.
- Alert events.
- Risk events.
- Analysis events.
- Prevention events.
- Duplicate events.
- Disconnect.
- Reconnect.
- Connection state indicators.

---

# 83. API Integration Tests

Test:

- Successful requests.
- Authentication failure.
- Authorization failure.
- Validation errors.
- Not found.
- Server error.
- Network failure.
- Timeout.
- Empty responses.
- Pagination.
- Filtering.

---

# 84. Security Tests

Test:

- XSS-safe rendering.
- Unsafe HTML payloads.
- Malicious query parameters.
- Authentication expiration.
- Unauthorized routes.
- Unauthorized API responses.
- Sensitive error suppression.
- Sensitive logging prevention.
- Invalid API response handling.

---

# 85. Responsive Testing

Verify the major application views at:

- Desktop.
- Laptop.
- Tablet.
- Mobile.

Test:

- Navigation.
- Tables.
- Charts.
- Cards.
- Forms.
- Dialogs.
- Alert details.
- Copilot interface.

No critical information should become inaccessible at smaller screen sizes.

---

# 86. Accessibility Testing

Verify:

- Keyboard navigation.
- Focus order.
- Button labels.
- Form labels.
- Dialog accessibility.
- Screen-reader labels.
- Severity labels.
- Chart descriptions.
- Error announcements.
- Real-time status announcements where appropriate.

---

# 87. Frontend Security Rules

The following rules are mandatory:

1. Never trust frontend authorization.
2. Never expose backend secrets.
3. Never expose database credentials.
4. Never fabricate security data.
5. Never independently calculate authoritative risk.
6. Never independently make prevention decisions.
7. Never bypass backend authorization.
8. Never allow unsafe organization switching.
9. Never render untrusted HTML without proper sanitization.
10. Never expose sensitive backend errors.
11. Never log authentication secrets.
12. Never treat AI output as authoritative system evidence.
13. Never claim an action was executed without backend confirmation.
14. Never allow real-time connection status to be falsely represented.
15. Never allow a frontend failure to alter core security decisions.

---

# 88. Guardrails

## Guardrail 01 — Backend Is the Source of Truth

The frontend only displays backend-owned security state.

---

## Guardrail 02 — No Client-Side Security Decisions

The frontend must not decide:

- Whether a voice is cloned.
- Whether a session is malicious.
- Whether risk is high.
- Whether an alert should exist.
- Whether prevention should occur.

---

## Guardrail 03 — No Cross-Tenant Access

Organization isolation must always be enforced by the backend.

---

## Guardrail 04 — No Fabricated Evidence

The UI must display only evidence returned by authorized backend services.

---

## Guardrail 05 — AI Output Is Not System Evidence

Security Copilot responses must be visually distinguishable from deterministic system records.

---

## Guardrail 06 — No Secret Exposure

Client-side code must never contain backend secrets.

---

## Guardrail 07 — Safe Rendering

All external or backend-provided text must be treated as untrusted.

---

## Guardrail 08 — Real-Time Failure Must Not Break Core UI

WebSocket failure must not prevent users from viewing already-loaded security information.

---

# 89. Definition of Done

Phase 11 is complete when:

- [ ] React frontend starts successfully.
- [ ] Production build succeeds.
- [ ] Authentication state is integrated.
- [ ] Protected routes work.
- [ ] Sidebar navigation works.
- [ ] Header works.
- [ ] Dashboard overview works.
- [ ] Security metrics are displayed from backend data.
- [ ] Risk distribution is displayed.
- [ ] Recent alerts are displayed.
- [ ] Recent analyses are displayed.
- [ ] Live activity is displayed.
- [ ] Analysis list works.
- [ ] Analysis detail works.
- [ ] Detection result interface works.
- [ ] Risk interface works.
- [ ] Alert center works.
- [ ] Alert detail works.
- [ ] Prevention interface works.
- [ ] Security Copilot interface works.
- [ ] REST API integration works.
- [ ] WebSocket integration works.
- [ ] Real-time events update relevant UI.
- [ ] WebSocket disconnect is handled.
- [ ] WebSocket reconnection is handled.
- [ ] Loading states exist.
- [ ] Empty states exist.
- [ ] Error states exist.
- [ ] Partial failures are handled.
- [ ] Responsive layouts work.
- [ ] Accessibility baseline is implemented.
- [ ] XSS-safe rendering is maintained.
- [ ] Sensitive information is not exposed.
- [ ] Frontend authorization UX is implemented.
- [ ] Tenant context is handled safely.
- [ ] Component tests pass.
- [ ] Page tests pass.
- [ ] API integration tests pass.
- [ ] WebSocket tests pass.
- [ ] Security-related frontend tests pass.

---

# 90. Phase Deliverables

| Deliverable | Expected Result |
|---|---|
| Application Shell | Complete dashboard layout |
| Navigation | Security module navigation |
| Dashboard Overview | Organization security summary |
| Analysis UI | Analysis monitoring and investigation |
| Detection UI | AI detection visualization |
| Risk UI | Risk assessment visualization |
| Alert Center | Security alert monitoring |
| Alert Details | Complete alert investigation |
| Prevention UI | Prevention/response history |
| Live Activity | Real-time event visualization |
| Security Copilot UI | AI security assistance interface |
| API Services | Centralized backend communication |
| WebSocket Client | Real-time event integration |
| Authentication UX | Authenticated application state |
| Authorization UX | Role-aware interface |
| Responsive UI | Desktop/tablet/mobile support |
| Accessibility | Accessible dashboard foundation |
| Error Handling | Controlled failure states |
| Testing | Frontend test coverage |

---

# 91. Final Dashboard Architecture

    ┌─────────────────────────────────────────────────────────────┐
    │                    SECURITY OPERATOR                        │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    REACT DASHBOARD                          │
    │                                                             │
    │  Dashboard   Analysis   Detection   Risk   Alerts           │
    │                                                             │
    │  Prevention   Copilot   Settings                            │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             ┌──────────────┐      ┌──────────────┐
             │   REST API   │      │  WebSocket   │
             └──────┬───────┘      └──────┬───────┘
                    │                     │
                    ▼                     ▼
             ┌──────────────┐      ┌──────────────┐
             │   Backend    │      │ Real-Time    │
             │   Services   │      │ Event System │
             └──────┬───────┘      └──────────────┘
                    │
                    ▼
             ┌──────────────┐
             │ PostgreSQL   │
             └──────────────┘

---

# 92. Complete Security Investigation Model

The dashboard must make the following relationship easy to understand:

    ┌──────────────┐
    │   Analysis   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Detection   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │     Risk     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    Alert     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Prevention  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   Copilot    │
    └──────────────┘

The operator should be able to navigate this entire chain from the dashboard.

---

# 93. Phase 11 Completion Statement

Phase 11 transforms the previously implemented backend security pipeline into a complete operator-facing security SaaS dashboard.

After Phase 11, the platform should provide a unified interface for:

    MONITOR
       ↓
    ANALYZE
       ↓
    DETECT
       ↓
    ASSESS RISK
       ↓
    INVESTIGATE
       ↓
    RESPOND
       ↓
    UNDERSTAND

The frontend must remain a presentation and interaction layer.

Authoritative security decisions remain inside backend services.

The final dashboard should provide a professional, responsive, secure and real-time experience without duplicating core security logic.

---

# 🏁 Phase 11 Final Acceptance

Phase 11 is accepted only when an authorized user can:

    1. Log in
       ↓
    2. Open the security dashboard
       ↓
    3. View current security metrics
       ↓
    4. Observe real-time activity
       ↓
    5. Open an analysis
       ↓
    6. Inspect detection results
       ↓
    7. Inspect risk assessment
       ↓
    8. Investigate the related alert
       ↓
    9. Review prevention decision/action
       ↓
    10. Ask Security Copilot for an explanation
       ↓
    11. Review evidence and recommendations
       ↓
    12. Return to the security overview

without losing authorization context, organization context, or investigation context.

**Phase 11 → COMPLETE**

**Next Phase → Phase 12 — Integration Testing**