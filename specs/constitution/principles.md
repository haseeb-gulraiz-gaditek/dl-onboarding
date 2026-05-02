# Product Principles

> Part of the Mesh Product Constitution

**Last amended:** 2026-05-02

---

## We Always

1. **Recommend honestly, including "skip this."** Even when a paid launch matches a profile, the concierge surfaces what's wrong with it alongside what's right. The moment users sense shilling, trust collapses — and trust is the only moat.
2. **Treat the user's profile as theirs.** Profile data is exportable in full; users can leave with everything they put in. No dark patterns to lock context inside Mesh.
3. **Separate organic recommendations from launch surfacing.** Storage stays separate (`tools_seed` for organic, `tools_founder_launched` for launches) and pipelines stay separate (organic ranking ignores launches). Launches MAY appear alongside organic recommendations when they clear the same match-quality threshold as the concierge nudge (top 5% / cosine > 0.85), but they are returned in a distinct `launches` slot — never commingled with the organic ranking signal. Founder payments never move an organic recommendation score.

  *Amended 2026-05-02 (C2): the original principle barred any cross-surface placement. Cycle #8 lit up the founder side; we accepted that genuinely well-matched launches earn the same right to be surfaced as organic picks, with the threshold gate (cycle #9) and the separated slot keeping "recommend honestly" intact.*

## We Never

1. **Never sell user-side advertising priced on impressions or clicks-without-engagement.** CPA on qualified engagement (click + dwell + downstream action) only. Impression-priced inventory destroys the targeting depth that justifies founder pricing.
2. **Never let founder accounts post in user communities.** Role-split is structural and non-transferable; we'd rather lose a founder's launch than blur the user/founder boundary that makes communities feel like users live there.
3. **Never grow user count by lowering profile-depth requirements.** Give-to-get is the entire mechanic. 500 deep profiles beat 50,000 shallow ones. If acquisition stalls, fix the value, not the questionnaire.

## We Prioritize (Ordered)

When two goods conflict, this is which wins:

1. **Honest recommendations over founder revenue.** If a paid launch is a poor fit for a user, the concierge says so.
2. **User profile depth over user volume.** Sharper recs from fewer users beats noisier recs from more users.
3. **Long-term trust over short-term engagement metrics.** No retention dark patterns; the export button always works; "skip" never costs the user anything.

## Design Tenets

1. **Tapping IS the ritual.** V1 UX is tap-to-answer cards, not chat. Speed of profile compounding > flexibility of free-form input. Chat is V1.5.
2. **Default to the user side.** When a feature could optimize for either side, choose users. Founder value scales with user-side trust, not the other way around.
3. **Anti-spam is structural, not enforced.** Role-split accounts, public invite tree, per-community karma — baked into the data model. We do not chase spam with moderation what we can prevent with structure.
