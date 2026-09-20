┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                PRESENTATION LAYER (FRONTEND)                           │
│  • React 18 + TypeScript + Vite (Deployed on Vercel Global Edge CDN)                   │
│  • Live Telemetry OCC Dashboard | Interactive Corridor & Delay Analytics (Recharts)   │
│  • Dynamic Month/Season Environmental Context Selector (September Monsoon, Winter Fog) │
└───────────────────────────────────────────▲────────────────────────────────────────────┘
                                            │
               Secure WebSocket (WSS) 30s Stream + HTTPS REST APIs (/api/*)
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                       BACKEND & SIMULATION SERVER (FASTAPI + UVICORN)                  │
│  Deployed on Render Cloud Service (Python 3.11 ASGI Engine)                            │
│                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              THE CLOSED-LOOP ENGINE                              │  │
│  │                                                                                  │  │
│  │   ┌───────────────────────────┐           ┌───────────────────────────┐          │  │
│  │   │        SYSTEM 1           │           │        SYSTEM 2           │          │  │
│  │   │  Kinematic Physics Engine │──────────▶│ ML Risk & ETA Forecaster  │          │  │
│  │   │  (Speed, Accel, Distance) │           │ (XGBoost + 1M+ Priors)    │          │  │
│  │   └─────────────▲─────────────┘           └─────────────┬─────────────┘          │  │
│  │                 │                                       │                        │  │
│  │                 │  Feedback Speed Cap                   │ High Hazard Condition  │  │
│  │                 │  (e.g., 45 km/h Monsoon)              │ (Fog / Congestion)     │  │
│  │                 │                                       ▼                        │  │
│  │   ┌─────────────┴─────────────┐           ┌───────────────────────────┐          │  │
│  │   │   PHYSICAL DECELERATION   │◀──────────│        SYSTEM 3           │          │  │
│  │   │   & SPEED RESTORATION     │           │ Dynamic Restriction Engine│          │  │
│  │   │  (Closed-Loop Kinematics) │           │ (Lifecycle: ACTIVE/EXPIRE)│          │  │
│  │   └───────────────────────────┘           └───────────────────────────┘          │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                       DATA & HISTORICAL CALIBRATION MATRIX                       │  │
│  │  • 1,000,000+ authentic IR historical section observations (NR + NCR zones)      │  │
│  │  • Empirical Bayesian Prior Matrix by Hour (0-23) & Season (Monsoon, Fog, etc.)  │  │
│  │  • Real Route Topologies: NDLS->DDN (315km), NDLS->AGC (195km), NDLS->LKO (511km) │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
