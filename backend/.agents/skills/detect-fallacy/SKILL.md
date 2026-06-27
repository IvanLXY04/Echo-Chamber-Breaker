---
name: detect-fallacy
description: |
  Evaluates an argument and identifies logical fallacies. Use this skill to score the user's debate input.
  Do NOT use to verify factual accuracy (use fact-checking tools for that).
version: 1.0.0
---

# Detect Fallacy Skill

## When to use
- Every time the user submits a new argument in the debate.

## Fallacies to Detect
1. **Ad Hominem:** Attacking the person rather than the argument.
2. **Straw Man:** Misrepresenting someone's argument to make it easier to attack.
3. **False Dilemma (Black and White Fallacy):** Presenting two alternative states as the only possibilities, when in fact more possibilities exist.
4. **Appeal to Emotion:** Manipulating an emotional response in place of a valid or compelling argument.

## Workflow
1. Read the user's argument carefully.
2. Scan for the presence of the fallacies listed above.
3. If a fallacy is detected, extract the exact quote where the fallacy occurred.
4. Formulate constructive feedback explaining *why* it is a fallacy and how to improve the argument.
5. Format the output to be consumed by the A2UI Scorecard.
