# Notes — Prompt Engineering Guidelines for Using LLMs in Requirements Engineering
**arXiv:2507.03405v1** | Ronanki, Arvidsson, Axell | Chalmers University of Technology / University of Gothenburg | July 4, 2025

---

## 1. What is this paper about?

The paper investigates whether existing **prompt engineering (PE) guidelines** — gathered from broad LLM literature — can be applied to **Requirements Engineering (RE)** activities. It does this through:
1. A **systematic literature review** of 28 primary studies → 36 PE guidelines extracted
2. **Interviews with 3 RE experts** to assess advantages and limitations
3. A **mapping** of the guidelines to 5 RE phases

The core gap it addresses: *no domain-specific PE guidelines exist for RE*.

---

## 2. Background & Motivation

- RE activities (elicitation, analysis, specification, validation, management) traditionally rely on NLP/ML approaches requiring large labelled datasets
- LLMs can reduce that dependency — but **prompt quality heavily affects output quality**
- Prompt engineering is the key lever, yet no structured guidance existed specifically for RE practitioners

---

## 3. Methodology

### 3.1 Systematic Literature Review
- Search string: `("Prompt Engineering" OR "Prompt Patterns" OR "Prompt Design") AND ("Large Language Models" OR "Generative AI")`
- Databases: ACM, Scopus, IEEE Xplore, ScienceDirect, arXiv
- Timeframe: 2018–present (post-transformer era)
- 271 papers screened → **28 included** → **36 guidelines extracted**

### 3.2 Expert Interviews
- 3 RE experts from different institutions (specialising in RE, AI4RE, NLP4RE)
- Semi-structured interviews, ~30 min each, conducted via Zoom
- Analysis: qualitative content analysis + thematic synthesis

---

## 4. The 36 Prompt Engineering Guidelines — 9 Themes

### C — Context (6 guidelines)
| ID | Guideline |
|----|-----------|
| C1 | Adding context to examples produces more efficient, informative output |
| C2 | Provide context to all prompts to avoid hallucinations |
| C3 | Context ensures closely related output |
| C4 | More context tokens → more fine-grained output |
| C5 | Context Manager Pattern: specify or remove context dynamically |
| C6 | More context + instructions → higher semantic quality |

### P — Persona (2 guidelines)
| ID | Guideline |
|----|-----------|
| P1 | Condition the prompt with an identity (e.g. "Python programmer", "Math tutor") to improve generation quality |
| P2 | Use "I want you to act as the system" + "Use the requirements to guide your behaviour" for RE exploration |

### T — Templates (3 guidelines)
| ID | Guideline |
|----|-----------|
| T1 | "Reason step-by-step for the following problem. [prompt]" improves reasoning and common sense |
| T2 | Art prompt template: `[Medium] [Subject] [Artist(s)] [Details] [Image repository support]` |
| T3 | "I am going to provide a template for your output; This is the template: PATTERN with PLACEHOLDERS" |

### D — Disambiguation (3 guidelines)
| ID | Guideline |
|----|-----------|
| D1 | Provide detailed scope: "Within this scope", "Consider these requirements or specifications" |
| D2 | "Point out any areas of ambiguity or potentially unintended outcomes" |
| D3 | Use persona prompting to explore ambiguities from multiple perspectives |

### R — Reasoning (5 guidelines)
| ID | Guideline |
|----|-----------|
| R1 | Prepend "Let's think step by step" → improves zero-shot performance |
| R2 | Extend to "Let's think step by step to reach the right conclusion" → highlights decision-making |
| R3 | Chain-of-Thought (CoT) prompting improves performance and factual consistency |
| R4 | Tree-of-Thought (ToT) enables deliberate multi-path decision making |
| R5 | Cognitive Verifier Pattern: force LLM to subdivide questions into sub-questions for better answers |

### A — Analysis (3 guidelines)
| ID | Guideline |
|----|-----------|
| A1 | Self-consistency boosts CoT performance |
| A2 | Best-of-three strategy improves output stability and hallucination detection |
| A3 | Emotion-enhanced CoT leverages emotional cues to improve mental health analysis tasks |

### K — Keywords (4 guidelines)
| ID | Guideline |
|----|-----------|
| K1 | Focus on subject and style keywords instead of connecting words |
| K2 | Pre-appending keywords greatly improves performance by providing appropriate context |
| K3 | Add modifier/keyword details to template sections |
| K4 | Multiple descriptive keywords align results closer to expectations |

### W — Wording (5 guidelines)
| ID | Guideline |
|----|-----------|
| W1 | In translation tasks, add a newline before the target-language phrase |
| W2 | Complete sentence definitions outperform stripped core-term sets |
| W3 | Words like "well-known" and "often used to explain" work well for analogy generation |
| W4 | Pseudocode-style prompts are most successful in coding tasks |
| W5 | Include explicit algorithmic hints in engineering task prompts |

### F — Few-shot Prompts (5 guidelines)
| ID | Guideline |
|----|-----------|
| F1 | Include "Question:" and "Answer:" labels — improves response but rarely gives binary answers |
| F2 | Number examples in few-shot prompting for clarity |
| F3 | [INPUT] and [OUTPUT] format should linguistically imply their relationship |
| F4 | Add specifications to each [INPUT]/[OUTPUT] pair for complex problems |
| F5 | Include a rationale in each shot: Input → Rationale → Output |

---

## 5. Mapping: Guidelines → RE Activities

| RE Phase | Applicable Guideline Themes |
|----------|-----------------------------|
| **Elicitation** | Context, Template, Keyword |
| **Analysis** | Template, Analysis, Reasoning |
| **Specification** | Persona, Disambiguation |
| **Validation** | Persona, Template |
| **Management** | Keyword, Reasoning |

### Key reasoning per phase
- **Elicitation**: Context prompts encourage creative requirements exploration; templates standardise the process; keywords help frame scope
- **Analysis**: Self-consistency (A1) and best-of-three (A2) address LLM output variability; CoT/ToT (R3/R4) strengthen reasoning
- **Specification**: Persona (P2) enables multi-perspective ambiguity exploration; D2 directly identifies weak or ambiguous requirements
- **Validation**: Persona helps validate against specific user needs; templates provide reusable, pre-validated prompt structures
- **Management**: Keywords assist sorting/classification/traceability; reasoning guidelines improve decision transparency

---

## 6. Expert Interview Insights

| RE Phase | Advantages noted | Limitations noted |
|----------|-----------------|-------------------|
| Elicitation | Context prompts spark creative requirements; templates useful across activities | "Context" is too generic a word; may not reflect what stakeholders actually want |
| Analysis | Could check qualities like "Is this maintainable?"; templates help completeness | High uncertainty in output; LLMs don't reason like RE practitioners |
| Specification | Iterative exploration of ambiguities; persona enables multi-angle review | Needs justifications for why a requirement is flagged |
| Validation | Persona useful for user-type validation; templates reusable | Insufficient LLM accuracy at this stage; too much system info needed |
| Management | Keywords aid sorting, classification, traceability | Keywords alone insufficient — deep domain knowledge also required |

---

## 7. Key Findings

- **36 guidelines extracted** from 28 studies, grouped into 9 themes
- **7 of 9 themes** are applicable to at least one RE activity (72% coverage)
- **Few-shot (F) and Wording (W)** guidelines were deemed **not relevant** to RE
- **Template** theme is the most broadly applicable — mapped to 3 of 5 RE phases
- **Context and Disambiguation**, while mapped to fewer phases, deliver **higher value** in the phases they do apply to
- Most guidelines appeared only **once** in the literature — the field is still maturing

---

## 8. Implications & Future Work

- Need for **RE-specific PE guidelines** — general ones are a starting point, not a solution
- Guidelines need validation across **broader, more diverse RE use cases**
- Potential to embed PE guidelines into **automated RE tooling** (e.g. AutoGPT-style pipelines)
- Future work: fine-tune existing guidelines for RE, or develop new domain-specific ones from scratch

---

## 9. Quick Reference — Most Useful Guidelines for Practice

| Goal | Use |
|------|-----|
| Prevent hallucinations | C2, C3 |
| Get richer, more specific output | C4, C6, K2, K4 |
| Improve reasoning quality | R1, R2, R3 (CoT), R4 (ToT) |
| Reduce ambiguity in RE tasks | D1, D2, D3 |
| Standardise prompt structure | T3 |
| Improve few-shot consistency | F2, F4, F5 |
| Frame a persona for RE tasks | P1, P2 |
| Improve output stability | A1 (self-consistency), A2 (best-of-3) |

---

*Paper: arXiv:2507.03405 — "Prompt Engineering Guidelines for Using Large Language Models in Requirements Engineering", Ronanki et al., 2025*