# GreenMind Implementation Notes

---

# 1. Project Vision

## GreenMind = Personal AI Usage Coach for Students

GreenMind is **not a normal Q&A chatbot**.

GreenMind helps students:

- understand the hidden environmental cost of AI
- analyze their AI usage habits
- estimate energy consumption
- estimate water usage
- estimate carbon emissions
- optimize prompting behavior
- reduce AI dependency
- become more sustainable AI users

---

# 2. System Architecture

```text
User
 ↓
Frontend (Streamlit)
 ↓
Backend (FastAPI)
 ↓
GreenMind Engine
    ├── Intent Detection
    ├── Usage Audit
    ├── Footprint Calculator
    ├── Prompt Optimizer
    ├── What-if Simulator
    ├── Eco Score Engine
    └── LLM Response Generator
```

---

# 3. Role of the LLM

## Use the LLM only for:

- natural language understanding
- intent detection
- prompt analysis
- coaching
- personalized explanations
- conversational flow

## Never use the LLM for:

- energy calculations
- CO₂ calculations
- water calculations
- scoring
- scientific numbers

These must come from Python backend.

---

# 4. System Prompt for LLM

```text
You are GreenMind, an AI Usage Coach for students.

Your job is to:

1. Understand natural student problems related to AI usage.

2. Detect inefficiencies such as:
   - excessive retries
   - vague prompts
   - fragmented prompting
   - overdependence on AI
   - excessive image generation
   - coding-heavy usage

3. Map the user's problem to one or more actions:
   - footprint calculation
   - usage audit
   - prompt optimization
   - what-if simulation
   - sustainability coaching

4. Never invent scientific numbers.

5. Use only backend-calculated values.

6. If required information is missing, ask follow-up questions.

7. Be supportive, concise, and educational.
```

---

# 5. Supported User Intents

GreenMind should detect:

## Productivity Issues

- time_inefficiency
- prompt_inefficiency
- frequent_regeneration
- bad_answers

## Sustainability Issues

- footprint_calculation
- sustainability_awareness

## Usage Analysis

- audit_request
- dependency_analysis

## Technical Usage

- coding_usage
- image_usage
- video_usage

## Optimization

- prompt_optimization
- what_if_simulation

---

# 6. Intent Extraction Prompt

```text
Analyze the user's message.

Classify into one or more of:

- time_inefficiency
- prompt_inefficiency
- footprint_calculation
- coding_usage
- image_usage
- dependency_analysis
- sustainability_awareness
- optimization_request

Return only JSON.
```

---

# Example

## User

I keep retrying ChatGPT all day.

## LLM Output

```json
{
  "intent": "prompt_inefficiency",
  "confidence": 0.95,
  "patterns": [
    "frequent_regeneration",
    "time_waste"
  ]
}
```

---

# 7. Baseline Environmental Values

## ChatGPT Text Query

Source:

- Epoch AI
- Sam Altman

Values:

```json
{
  "energy_wh": 0.34,
  "co2_g": 0.05,
  "water_ml": 10
}
```

---

## Coding Request

```json
{
  "energy_wh": 0.5,
  "co2_g": 0.07,
  "water_ml": 0.8
}
```

---

## Image Generation

```json
{
  "energy_wh": 2.0,
  "co2_g": 0.3,
  "water_ml": 5
}
```

---

# 8. Eco Score Engine

## Base Score

```text
100
```

---

# Penalty Rules

## Prompts Per Day

| Usage | Penalty |
|------|------|
| 0–15 | 0 |
| 16–30 | -10 |
| 31–50 | -20 |
| >50 | -30 |

---

## Regenerations

| Usage | Penalty |
|------|------|
| 0–2 | 0 |
| 3–5 | -10 |
| 6–10 | -20 |
| >10 | -30 |

---

## Images Per Week

| Usage | Penalty |
|------|------|
| 0–2 | 0 |
| 3–5 | -10 |
| 6–10 | -20 |
| >10 | -30 |

---

## Coding Requests Per Day

| Usage | Penalty |
|------|------|
| 0–5 | 0 |
| 6–10 | -5 |
| >10 | -10 |

---

# Prompt Quality

## Vague prompt

Penalty:

```text
-10
```

## Fragmented prompt

Penalty:

```text
-15
```

## Structured prompt

Bonus:

```text
+10
```

---

# Dependency Risk

High dependency:

```text
-15
```

---

# Final Formula

```text
Green Score =
100
- prompt_penalty
- retry_penalty
- image_penalty
- coding_penalty
- dependency_penalty
+ efficiency_bonus
```

Clamp:

```text
0–100
```

---

# Score Labels

| Score | Label |
|------|------|
| 90–100 | Eco Expert �� |
| 75–89 | Efficient User ✅ |
| 50–74 | Moderate User ⚠ |
| 25–49 | Wasteful Usage �� |
| 0–24 | High Impact User �� |

---

# Example Calculation

## User

- 35 prompts/day
- 8 regenerations
- 5 images/week
- 12 coding requests/day
- vague prompts

---

## Score

```text
100
-20
-20
-10
-10
-10
```

## Final Score

```text
30/100
```

---

# 9. Prompt Optimization Prompt

```text
You are GreenMind.

Analyze the student's prompt.

Tasks:

1. Identify inefficiencies.
2. Explain why retries may happen.
3. Rewrite it as a sustainable prompt.
4. Estimate reduction in follow-up prompts.
```

---

# Example

## User Prompt

Explain machine learning.

---

## GreenMind

Problems:

- too broad
- no audience
- no output constraints

Optimized Prompt:

Explain machine learning in 200 words for an engineering student, include one real-world example, and summarize the key ideas in 3 bullet points.

Potential reduction:

30–40%

---

# 10. Professor Pitch

Say this exactly:

GreenMind is not a command-based chatbot.

It acts as an interactive AI usage coach that understands natural student problems, analyzes prompting behavior, estimates environmental impact, assigns an explainable Eco Score, and provides personalized sustainability coaching.

The language model is used only for natural language understanding and coaching, while all sustainability calculations and scoring are generated using a transparent rule-based backend.