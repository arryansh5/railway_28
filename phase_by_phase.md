# SUPERNOVA — MASTER BACKEND IMPLEMENTATION PROMPT
# Railway Journey Simulation + ETA Intelligence + Real-World Validation

You are working on the backend of the Supernova railway ETA intelligence system.

IMPORTANT:
DO NOT build or redesign the frontend.
DO NOT modify unrelated frontend code.
DO NOT implement all phases at once.
Work strictly phase-by-phase.
After each phase, run tests, report results, and STOP for approval before moving to the next phase.

============================================================
1. PRODUCT OBJECTIVE
============================================================

Supernova is a railway ETA intelligence system.

The core objective is:

Given the current state of a train, its remaining railway route, historical railway behavior, and current contextual conditions, estimate the remaining travel time and predicted arrival time.

The backend architecture consists of:

HISTORICAL WORLD
    ↓
SYSTEM 1 — JOURNEY / WORLD SIMULATOR
    ↓
SYNTHETIC JOURNEY TRAJECTORIES
    ↓
ETA TRAINING DATASET
    ↓
SYSTEM 2 — ETA XGBOOST MODEL
    ↓
LIVE ETA
    ↓
RAILRADAR / REAL-TIME OBSERVATIONS
    ↓
REAL-WORLD VALIDATION
    ↓
CALIBRATION
    ↓
SYSTEM 1 / SYSTEM 2

System 3 is NOT part of the core architecture.
Do not build a separate decision engine unless explicitly requested later.

============================================================
2. CORE ARCHITECTURAL PRINCIPLE
============================================================

Use three conceptual worlds:

1. HISTORICAL WORLD
   "What normally happened?"

   Source:
   Historical Kaggle data.

2. SIMULATED WORLD
   "How could this journey plausibly unfold?"

   Source:
   System 1.

3. REAL WORLD
   "What is actually happening?"

   Source:
   RailRadar and other legitimate real-time observations.

System 2 connects current state to remaining travel time.

IMPORTANT TERMINOLOGY:

Do NOT say:
"System 1 predicts the exact future."

Instead say:
"System 1 generates statistically plausible future journey trajectories based on historical railway behavior, network structure, and scenario conditions."

System 2 predicts:
"remaining travel time from the current state."

============================================================
3. DATA SOURCES AND THEIR PURPOSES
============================================================

There are FOUR distinct data categories.

------------------------------------------------------------
A. KAGGLE TRAIN DATA
------------------------------------------------------------

Purpose:
Learn historical railway behavior.

Use it for:
- historical behavior analysis
- feature analysis
- baseline modeling
- simulator calibration
- deriving behavioral distributions where justified

Do NOT treat every feature as automatically causal.

Do NOT invent relationships that are not supported by data.

------------------------------------------------------------
B. KAGGLE TEST DATA
------------------------------------------------------------

Purpose:
Held-out evaluation for the task and targets actually represented in the Kaggle dataset.

IMPORTANT:

Do NOT automatically treat Kaggle test data as an ETA test set.

If the Kaggle test set does not contain:
- trajectory states
- actual remaining travel time
- actual arrival outcome

then it cannot directly evaluate the new ETA target.

Use it only for evaluation that its actual labels support.

Never invent ETA ground truth from unavailable fields.

------------------------------------------------------------
C. SYSTEM 1 SYNTHETIC DATA
------------------------------------------------------------

Purpose:
Generate complete plausible railway journeys and ETA training scenarios.

Synthetic data is NOT ground truth.

Every synthetic row must retain:

data_origin = "synthetic"

------------------------------------------------------------
D. REAL-TIME / REAL OBSERVATION DATA
------------------------------------------------------------

Primary current observation source:
RailRadar.

Purpose:
- current train state
- current position
- current speed
- current delay
- current journey progress
- live validation
- actual journey outcome where legitimately observable

RailRadar is an external observation provider.

DO NOT call RailRadar:
- Indian Railways official ground truth
- official RTIS
- guaranteed ground truth

Preserve data provenance.

============================================================
4. CORE SYSTEM RESPONSIBILITIES
============================================================

------------------------------------------------------------
SYSTEM 1 — JOURNEY / WORLD SIMULATOR
------------------------------------------------------------

Purpose:

Generate complete, statistically plausible railway journey trajectories.

System 1 should answer:

"What could happen from here?"

Inputs may include:

- train characteristics
- origin
- destination
- dynamically resolved route
- departure time
- historical behavioral distributions
- railway network structure
- environmental/contextual conditions
- operational scenario
- relevant historical features

Outputs:

- timestamp
- position/state
- section
- speed/state
- delay
- station events
- dwell
- remaining distance
- remaining stops
- journey progress
- destination arrival

System 1 is a simulation engine.

Do NOT make System 1 a single black-box XGBoost model that magically predicts an entire trajectory.

Instead:

Behavioral model(s)
+
Railway network
+
State-transition logic
+
Stochastic variation
=
System 1

XGBoost may be used inside System 1 for specific behavioral predictions if justified by available data.

------------------------------------------------------------
SYSTEM 2 — ETA XGBOOST
------------------------------------------------------------

Purpose:

Predict:

actual_remaining_travel_time_minutes

System 2 should answer:

"Given everything known about the train NOW, how much time is likely to remain?"

Primary target:

actual_remaining_travel_time_minutes

Do NOT make arrival timestamp the primary ML target.

Arrival timestamp should be derived:

predicted_arrival_time =
current_timestamp + predicted_remaining_minutes

System 2 does NOT simulate the railway.

It predicts the remaining travel time from a current state.

------------------------------------------------------------
RAILRADAR
------------------------------------------------------------

RailRadar provides observations.

Conceptually:

RailRadar
    ↓
Current train state
    ↓
Network matching
    ↓
Remaining route
    ↓
System 2
    ↓
Live ETA

Every meaningful new real-time state may trigger a fresh ETA prediction.

The model does not need to be retrained after every observation.

State changes.
Model remains fixed until a deliberate retraining/calibration cycle.

============================================================
5. GLOBAL RULES
============================================================

RULE 1:
Never invent railway facts.

Do not invent:
- station codes
- coordinates
- distances
- route relationships
- speed limits
- electrification
- track characteristics
- dwell times
- weather effects
- operational rules

If unavailable:
mark as missing/unverified/pending verification.

RULE 2:
Never silently convert assumptions into facts.

Every important value must be classified as:

- observed
- historical
- learned
- derived
- static
- simulated
- scenario assumption
- unknown

RULE 3:
Prevent leakage.

Only use information that would have been available at prediction time.

Do not use:
- future outcome
- future delay
- post-arrival information
- post-event delay causes
- future observations

when constructing prediction features.

RULE 4:
Preserve provenance.

Important records should include fields such as:

source
observed_at
received_at
data_origin
source_record_id
raw_payload
quality/status

RULE 5:
Do not overfit to synthetic data.

Synthetic data is scenario coverage and training support.

It is not ground truth.

RULE 6:
Real observations are used to validate the system.

The system must measure:

prediction
vs
actual observed outcome

RULE 7:
Do not modify unrelated code.

Only modify files/components necessary for the current phase.

RULE 8:
Do not build frontend features.

The frontend is outside the scope of this implementation plan.

============================================================
6. PHASE PLAN
============================================================

============================================================
PHASE 0 — BACKEND AUDIT AND CONTRACT
============================================================

Goal:

Understand the existing backend before changing anything.

Inspect:

- backend framework
- database
- models
- APIs
- existing train state logic
- existing simulator
- existing prediction code
- existing RailRadar integration
- existing ML pipelines

Create a backend architecture report:

1. Existing components
2. Components to keep
3. Components to modify
4. Components to add
5. Existing technical debt
6. Existing API contracts
7. Existing database structures

Do NOT build new ML.

Do NOT redesign the frontend.

Deliverable:

backend_audit.md

STOP after completion.

============================================================
PHASE 1 — KAGGLE DATA AUDIT
============================================================

Goal:

Understand exactly what the Kaggle data can teach us.

Analyze BOTH:

- Kaggle train dataset
- Kaggle test dataset

Feature list:

TRAIN / SERVICE
train_type
train_number

TIME
year
month
day_of_week
departure_hour
is_weekend
is_night_departure
is_peak_hour
is_festival_season
season

GEOGRAPHY
zone
source_station_category
destination_station_category

ROUTE
distance_km
num_scheduled_stops
scheduled_travel_hours
track_doubled
is_hdn_route
traction_type
is_electrified
psr_count
is_circular_route

WEATHER
is_monsoon_season
is_fog_risk
fog_risk_score
zone_fog_index
zone_congestion_index
season_severity_score

ROLLING STOCK
loco_age_years
coach_age_years
has_lhb_coaches
is_rake_shared
maintenance_score

OPERATIONS
seat_utilisation_pct
is_overloaded
late_incoming_rake
is_special_train
route_historical_ontime_pct

For each feature determine:

- semantic meaning
- data type
- missingness
- cardinality
- static/historical/dynamic/derived
- prediction-time availability
- potential leakage
- suitable system ownership
- whether usable for System 1
- whether usable for System 2
- whether usable live
- whether it needs transformation

Create:

historical_feature_dictionary

Also document:
- target columns
- train/test schema differences
- date coverage
- train coverage
- route coverage
- possible duplicates
- suspicious features
- leakage risks

Do NOT train System 2.

STOP.

============================================================
PHASE 2 — KAGGLE BASELINE
============================================================

Goal:

Establish what the historical Kaggle problem itself can predict.

Use appropriate train/test separation.

Do NOT confuse this baseline with System 2 ETA.

Evaluate only targets actually supported by the Kaggle dataset.

Document:

- preprocessing
- features
- model
- metric
- train/test behavior
- leakage controls

Use journey-aware or chronological validation where appropriate.

Do not blindly reproduce shuffled validation if it risks journey leakage.

Deliverable:

kaggle_baseline_report.md

STOP.

============================================================
PHASE 3 — RAILWAY NETWORK GRAPH
============================================================

Build:

stations
sections
routes
route_sections

Architecture:

Stations = nodes
Physical railway sections = edges
Routes = ordered station/section relationships

A physical section should not be duplicated merely because direction changes.

Example:

Roorkee ↔ Haridwar

supports:

Roorkee → Haridwar
Haridwar → Roorkee

Use one physical section.

Preserve:

source_document
source_reference
needs_verification
data_quality

Do not invent missing network information.

STOP.

============================================================
PHASE 4 — DYNAMIC ROUTE RESOLVER
============================================================

Implement:

resolve_route(origin_station, destination_station)

Return:

- ordered stations
- ordered sections
- direction
- total distance where known
- remaining distance support
- route metadata
- ambiguity status

Test:

Delhi → Roorkee
Roorkee → Dehradun
Dehradun → Roorkee
Delhi → Dehradun

Handle:

- unknown stations
- ambiguous stations
- no route
- multiple possible paths

Do not silently select arbitrary routes when ambiguity exists.

STOP.

============================================================
PHASE 5 — HISTORICAL BEHAVIOR ENGINE
============================================================

Goal:

Convert historical evidence into behavioral knowledge for System 1.

Learn only relationships supported by data.

Potential behavioral outputs:

- journey duration distributions
- delay distributions
- train-type behavior
- temporal behavior
- seasonal behavior
- route-level behavior
- operational behavior
- weather/risk-conditioned behavior where justified

Do not hard-code:

"fog = +10 minutes"

unless supported by learned/calibrated evidence.

Prefer distributions over fixed constants.

Example conceptual form:

P(travel_time | route, train_type, time, context)

Deliverable:

HistoricalBehaviorService

STOP.

============================================================
PHASE 6 — SYSTEM 1 SIMULATOR CORE
============================================================

Build the journey simulator.

Input:

- train
- origin
- destination
- departure time
- route
- historical behavior
- contextual conditions
- operational scenario

Simulation:

Origin
↓
section movement
↓
state transition
↓
station arrival
↓
dwell
↓
next section
↓
repeat
↓
destination

Generate complete trajectories.

Retain raw simulation states.

Suggested raw simulation cadence:

30 seconds

But keep the cadence configurable.

Each state should contain, where available:

timestamp
train_id
journey_id
station/section
position
speed
delay
direction
station status
remaining distance
remaining stops
context
data_origin = synthetic

STOP.

============================================================
PHASE 7 — SYSTEM 1 REALISM / CALIBRATION TEST
============================================================

Before training System 2, test whether System 1 is plausible.

Compare available simulation outputs against historical evidence.

Evaluate:

- journey duration distributions
- delay distributions
- route behavior
- train-type behavior
- temporal behavior
- station dwell if supported
- section behavior if supported

Do not claim exact realism.

Document:

- learned behavior
- assumptions
- limitations
- unsupported quantities

If System 1 is obviously unrealistic:

FIX SYSTEM 1.

Do not proceed just because it generates data.

STOP.

============================================================
PHASE 8 — ETA DATASET GENERATOR
============================================================

Convert complete System 1 trajectories into ETA training examples.

Core rule:

ONE ROW = ONE ETA PREDICTION OPPORTUNITY.

For each snapshot calculate:

Current state:
- timestamp
- current position
- current section
- speed
- delay
- movement state

Remaining journey:
- remaining distance
- remaining stops
- remaining sections
- scheduled remaining time where available

Context:
- train characteristics
- temporal features
- weather/context
- operational features
- historical behavior

Target:

actual_remaining_travel_time_minutes

This target is calculated from the simulated trajectory's actual destination arrival.

Keep:

data_origin = synthetic

Do NOT necessarily use every 30-second observation as an ETA training row.

Allow:
- regular snapshots
- event-triggered snapshots

Deliver:

synthetic_eta_training_dataset

STOP.

============================================================
PHASE 9 — SYNTHETIC + REAL DATA STRATEGY
============================================================

Before System 2 training, explicitly separate:

Kaggle historical data
System 1 synthetic data
Real observations
Kaggle test data

Define what each dataset is allowed to do.

Synthetic data:
- scenario coverage
- training support
- rare conditions
- controlled experiments

Real observations:
- reality reference
- validation
- calibration

Kaggle test:
- only evaluate targets actually represented by its labels

Do not pretend Kaggle test provides ETA ground truth if it does not.

Preserve:

data_origin

Possible values:

kaggle
synthetic
realtime
observed

Document the training strategy.

STOP.

============================================================
PHASE 10 — SYSTEM 2 ETA XGBOOST
============================================================

Train XGBoost regression.

Target:

actual_remaining_travel_time_minutes

Input:

Current state
+
Remaining journey
+
Historical behavior
+
Train characteristics
+
Temporal context
+
Weather/context
+
Operational context

Do not make arrival timestamp the primary target.

Generate:

predicted_remaining_travel_time_minutes

Then derive:

predicted_arrival_time

Do not use post-outcome features.

STOP.

============================================================
PHASE 11 — SYSTEM 2 OFFLINE VALIDATION
============================================================

Evaluate:

MAE
RMSE
median absolute error
error distribution
bias

Use journey-level separation.

Never put snapshots from the same journey into both train and validation.

Test robustness across:

- route
- train type
- delay bucket
- time
- context

Document limitations.

STOP.

============================================================
PHASE 12 — REAL-TIME OBSERVATION PROVIDER
============================================================

Integrate RailRadar through an abstraction.

Create:

ObservationProvider

Implement:

RailRadarObservationProvider

Normalize into:

LiveTrainObservation

Fields may include:

observation_id
train_number
journey_date
timestamp
source
source_record_id
latitude
longitude
speed_kmph
bearing
delay_minutes
next_station_id
section_id
status
raw_payload
observed_at
received_at

Do not expose API keys to frontend.

Preserve raw provider payload server-side where appropriate.

STOP.

============================================================
PHASE 13 — LIVE JOURNEY RECONSTRUCTION
============================================================

Map real observations to the railway graph.

Pipeline:

RailRadar position
↓
station/section matching
↓
direction
↓
route matching
↓
remaining sections
↓
remaining distance
↓
current train state

Handle:

- GPS uncertainty
- ambiguous station matching
- missing coordinates
- stale observations
- missing speed
- route ambiguity

Do not silently produce a false precise position.

STOP.

============================================================
PHASE 14 — LIVE ETA ENGINE
============================================================

Connect:

RailRadar
+
Network
+
Remaining route
+
Historical behavior
+
Current context
↓
System 2
↓
Live ETA

Example:

current timestamp = 18:40
predicted remaining time = 58 minutes

predicted arrival = 19:38

The model is not retrained for every observation.

Only inference is repeated.

STOP.

============================================================
PHASE 15 — REAL-WORLD ETA VALIDATION
============================================================

For real journeys:

Record:

prediction_timestamp
predicted_remaining_minutes
predicted_arrival_time
actual_arrival_time
prediction_error
source
journey_id

Calculate:

MAE
RMSE
bias
error distribution

Analyze errors by:

- route
- train type
- initial delay
- weather/context
- time
- remaining distance

Be explicit that RailRadar is an external observation source and may have limitations.

STOP.

============================================================
PHASE 16 — CALIBRATION LOOP
============================================================

Use accumulated real-world errors to determine:

- simulator mismatch
- ETA model mismatch
- missing features
- network matching problems
- observation quality problems
- systematic bias

Do not blindly add arbitrary correction constants.

Determine which component is responsible.

Update:

System 1 behavioral distributions
and/or
System 2 model/features
and/or
observation processing

through controlled retraining/calibration.

STOP.

============================================================
PHASE 17 — COMPLETE BACKEND CLOSED LOOP
============================================================

Integrate the full backend:

Historical Kaggle
↓
Historical Behavior
↓
System 1
↓
Synthetic Journey
↓
ETA Dataset
↓
System 2
↓
RailRadar
↓
Current State
↓
Live ETA
↓
Actual Outcome
↓
Validation
↓
Calibration
↓
System 1 / System 2

Test one complete journey end-to-end.

Preferred demonstration:

Roorkee → Dehradun

or another fully supported route.

STOP.

============================================================
PHASE 18 — OPTIONAL COUNTERFACTUAL SIMULATION
============================================================

Only implement if needed.

Use System 1 to answer:

"What could happen if a condition changes?"

Examples:

- increased congestion
- reduced dwell
- weather change
- operational scenario

Do NOT claim operational recommendations.

Do NOT build System 3 unless explicitly requested.

STOP.

============================================================
PHASE 19 — BACKEND QA
============================================================

Test:

NETWORK
- station lookup
- route resolution
- reverse routes
- ambiguity

SYSTEM 1
- complete journeys
- reproducibility with seeds
- stochastic variation
- impossible-state detection

SYSTEM 2
- feature generation
- inference
- missing features
- model loading

LIVE
- RailRadar failures
- stale observations
- invalid train
- provider outage

VALIDATION
- actual arrival
- prediction error
- aggregation

DATA
- provenance
- synthetic vs real separation
- leakage prevention

SECURITY
- API keys server-side
- no sensitive secrets in logs

STOP.

============================================================
PHASE 20 — BACKEND DEMO CONTRACT
============================================================

Expose clean backend interfaces.

Possible endpoints:

POST /routes/resolve
GET /trains/{train_id}/state
POST /simulation/journey
POST /simulation/scenario
POST /eta/predict
GET /eta/{train_id}
POST /observations/railradar
GET /validation/{journey_id}
GET /calibration/report

Exact endpoint naming must follow the existing backend conventions.

Do not redesign frontend.

============================================================
7. REQUIRED DEVELOPMENT BEHAVIOR
============================================================

For EVERY phase:

1. Inspect existing implementation first.
2. Explain what will be changed.
3. Implement only the current phase.
4. Do not silently modify unrelated systems.
5. Run tests.
6. Show changed files.
7. Show validation results.
8. Document assumptions.
9. Identify unresolved issues.
10. STOP and wait for approval.

Never implement Phase N+1 automatically.

============================================================
8. FINAL ARCHITECTURE TO PRESERVE
============================================================

                 HISTORICAL KAGGLE DATA
                          │
                          ▼
                 HISTORICAL BEHAVIOR
                          │
                          ▼
                 ┌─────────────────┐
                 │    SYSTEM 1     │
                 │ JOURNEY/WORLD   │
                 │    SIMULATOR    │
                 └────────┬────────┘
                          │
                  synthetic journeys
                          │
                          ▼
                    ETA DATASET
                          │
                          ▼
                 ┌─────────────────┐
                 │    SYSTEM 2     │
                 │   ETA XGBOOST   │
                 └────────┬────────┘
                          │
                       LIVE ETA
                          │
                          ▼
                     RAILRADAR
                          │
                    current state
                          │
                          ▼
                      VALIDATE
                          │
                          ▼
                     CALIBRATE
                          │
                          └──────→ SYSTEM 1 / SYSTEM 2

Core principle:

SYSTEM 1 = "What could happen?"
SYSTEM 2 = "How much time remains?"
RAILRADAR = "What is happening?"
VALIDATION = "How close were we?"
CALIBRATION = "How do we improve?"

Do not collapse these responsibilities.

============================================================
9. FINAL SUCCESS CRITERIA
============================================================

The backend is considered successful only when:

1. Arbitrary supported origin/destination routes can be resolved.
2. System 1 can generate a complete plausible journey.
3. System 1 outputs state trajectories.
4. Synthetic trajectories can become ETA training examples.
5. System 2 predicts remaining travel time.
6. RailRadar observations can be mapped to the railway network.
7. System 2 can produce live ETA from real state.
8. Predictions can be compared against actual outcomes.
9. Validation metrics can be calculated.
10. Calibration can improve the appropriate component.
11. Synthetic and real data remain distinguishable.
12. Kaggle train/test roles remain clearly separated.
13. No leakage is introduced.
14. No unsupported railway facts are invented.
15. The backend works without requiring the frontend.

IMPORTANT:

Do not optimize for architectural complexity.

Build the smallest backend that proves:

HISTORICAL BEHAVIOR
        ↓
SIMULATED JOURNEY
        ↓
ETA MODEL
        ↓
REAL TRAIN STATE
        ↓
LIVE ETA
        ↓
REAL-WORLD VALIDATION

That is the core Supernova system.