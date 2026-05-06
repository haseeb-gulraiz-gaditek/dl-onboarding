# Approach 1 — validation experiment

Standalone implementation of the hand-tagged 6-dim feature scorer from
`validation/approaches.md`. Runs against the 3 locked personas
(`validation/onboarding-v1-locked.md`) and dumps a top-10 report you
can eyeball.

**Not wired into the FastAPI app.** See `integration_plan.md` for the
plug-in roadmap once metrics look good.

## Files

| File | Purpose |
|---|---|
| `schema.py` | Closed-vocabulary enums for the 6 feature dims |
| `tag_features.py` | One-shot script: reads `tools_seed` from Mongo, calls OpenAI gpt-4o-mini to tag each tool, writes `catalog_features.json` |
| `catalog_features.json` | Output of the tagger — 546 tools × 9 fields each |
| `feature_scorer.py` | The Approach 1 scorer (UserVector dataclass + `score_tool`/`rank_tools`) |
| `personas.py` | The 3 locked personas as progressive UserVectors (post-Q1, Q2, Q3, Q4) |
| `run.py` | Runs all 3 personas through Q1→Q4 narrowing, writes `results.md` |
| `results.md` | Output of `run.py` — top-10 per persona at each step |
| `integration_plan.md` | How this would plug into the FastAPI app |

## Running it

```bash
cd /home/haseeb/dl-onboarding
source venv/bin/activate

# Step 1: tag the catalog (~2 min, ~$0.15 of OpenAI). Resumable.
python -m validation.approach1.tag_features

# Step 2: run the personas (~2 sec, no API calls)
python -m validation.approach1.run

# Step 3: read the report
$EDITOR validation/approach1/results.md
```

## Known limitations of this validation cut

1. **Soft narrowing is not implemented.** Each step filters from the
   previous step's surviving set; the doc spec wants re-scoring the
   *full catalog* every step. Easy fix; deferred to integration.
2. **Equal weights.** Hand-tuned weights need a grid search against
   eyeballed gold ranks.
3. **Catalog coverage.** Vertical AI tools (Suki, DataSnipper,
   MindBridge, etc.) aren't in `tools_seed` yet. Ranking is only as
   good as the catalog admits.
