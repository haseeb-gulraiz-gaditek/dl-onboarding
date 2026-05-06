# Onboarding question variants — 3 different philosophies

All three are **MCQ-only** (no typing), 12 questions each, designed so the *option-pick itself* reveals industry + daily ops + paradigm without ever asking "what's your job?" directly.

**Personas used for walkthroughs**:
- **ACCA** — senior accountant at a midsize firm, audit & advisory, lives in Excel + Sharepoint
- **SWE** — backend engineer at a SaaS startup, Python + Postgres, GitHub + Linear
- **Doctor** — family medicine, hospital + outpatient, Epic EHR + a lot of paper

---

## Variant A — "Day in the life"

**Premise**: anchor every question on a concrete moment in the user's actual workday. The picks reveal industry through behavior, not labels.

| # | Question | Options (tap one unless noted) |
|---|---|---|
| 1 | First thing you open when work starts? | Email · Slack/Teams · Code editor · Note app/to-do · Client portal · Excel/Sheets · Calendar · No routine |
| 2 | Last thing you finished yesterday? | Status update/report · Closed tickets/shipped code · Reviewed a doc · Cleaned meeting notes · Reconciled numbers · Saw last patient/signed charts · Replied to clients · Just stopped |
| 3 | What eats more time than it should? | Repeating same explanation · Switching 5+ apps · Looking up what I already wrote · Formatting docs · Manual data entry across systems · Meetings that should be messages · Catching up after offline |
| 4 | How is your work mostly delivered? | Shared doc · Spreadsheet/dashboard · Running code · A decision · A consultation/conversation · A scheduled task · A presentation |
| 5 | Where does your important stuff actually live? | Notion/Confluence · Drive/Sharepoint · Excel · Email + attachments · Code repo · CRM/EHR/ERP · Notebook/sticky notes · Scattered |
| 6 | Pick the one that bugs you most | Same email/report patterns · Lose context when switching tasks · Can't find past work · New tools don't fit · Doing manual work AI could do · Miss things in meetings |
| 7 | When you've tried AI tools, what usually happens? | Haven't tried · Sounded smart, wasn't useful · I use one for everything · A few specialized ones consistently · Tried 5+, abandoned most · I use them but don't trust output |
| 8 | Tools you abandoned in last 6 months *(multi)* | ChatGPT sub · Notion AI · Zapier/Make · Meeting recorder · Custom GPT · "AI for X" startup · Excel/Sheets plugin · Coding assistant · None · Other |
| 9 | Where should AI live to actually help? | Inside the app I'm in · A separate tab I open · Background, no UI · Voice assistant · Doesn't matter |
| 10 | What matters MOST when picking a new tool? | Works instantly · Plugs into my stack · Learns my style · I can trust output without checking · Saves 30+ min per use · Cheap |
| 11 | If a tool replaced ONE recurring task you hate? | Reformatting/cleaning data · First-draft writing · Summarizing long things · Looking up past info · Translating between formats · Generating reports · Catching up · Making decisions faster |
| 12 | Patience for setup? | 30s · 5 min · 15 min · 1 hr · Want someone else to set up |

### Walkthrough

**ACCA picks**: Q1=Excel · Q2=Reconciled numbers · Q3=Manual data entry · Q4=Spreadsheet · Q5=Excel + Sharepoint · Q6=Same report patterns · Q7=Sounded smart, wasn't useful · Q8=ChatGPT sub + Excel plugin · Q9=Inside the app · Q10=Plugs into my stack · Q11=Generating reports · Q12=5 min

**→ Profile inferred** (no explicit "I'm an accountant" needed): Excel-native, audit/reporting workflow, low AI maturity, integration-first paradigm, abandoned generic AI for specificity reasons. Recommend: Excel-native AI plugins (Numerous.ai, Rows AI), report-generation tools (Causal, Cube), strict no-generic-chat tools.

**SWE picks**: Q1=Code editor · Q2=Closed tickets · Q3=Switching apps · Q4=Running code · Q5=Code repo · Q6=Lose context when switching · Q7=A few specialized ones · Q8=Custom GPT + meeting recorder · Q9=Inside the app · Q10=Plugs into my stack · Q11=Looking up past info · Q12=15 min

**→ Profile inferred**: backend dev, multi-app workflow, intermediate AI maturity, integration-first, knowledge-management gap. Recommend: IDE-native AI (Cursor, Continue), code search (Sourcegraph Cody), Linear/GitHub-native tools, NOT another standalone chat.

**Doctor picks**: Q1=Calendar · Q2=Saw last patient · Q3=Catching up after offline · Q4=A consultation · Q5=EHR · Q6=Miss things in meetings · Q7=Haven't tried · Q8=None · Q9=Background, no UI · Q10=Works instantly · Q11=Catching up · Q12=30s

**→ Profile inferred**: clinical workflow, very low AI maturity, EHR-locked, time-starved, zero patience for setup. Recommend: ambient scribe (Abridge, Suki), inbox-summarization (Doximity GPT-style), avoid anything requiring config.

---

## Variant B — "Picture your screen"

**Premise**: ask about visible artifacts (tabs, files, dock icons, monitors). Picks fingerprint the industry through environment.

| # | Question | Options |
|---|---|---|
| 1 | How many browser tabs open right now? | 1–3 · 4–10 · 10–30 · 30+ · I don't use tabs |
| 2 | What's pinned in your dock/taskbar? *(multi)* | Email/Calendar · Slack/Teams · Code editor · Excel/Sheets · Browser · Design app (Figma/PS) · Industry app (EHR/CRM/ERP) · Note app · Meeting tool · ChatGPT/Claude |
| 3 | Your second monitor mostly shows? | Reference docs/PDFs · Slack/Email · Logs/dashboards · A doc I'm writing on the main · Video meeting · Calendar/to-do · I don't use one |
| 4 | File extension you open most? | .xlsx/.csv · .docx/.pdf · .py/.js/.sql · .pptx · Image files · Mostly browser apps · Industry-specific (.dwg, EHR, etc.) |
| 5 | Which chart shows your day? | Long focus blocks · Meetings everywhere · Reactive (whatever pops up) · Routine (same times) · Half meetings, half deep · Waiting on others |
| 6 | When you're stuck, FIRST move? | Google · ChatGPT/Claude · Ask a colleague · Internal docs · Official docs · Figure it out alone · Ask manager |
| 7 | Most-used keyboard shortcut? | Copy/paste · Save · New tab · Find · Switch app · Undo · Vim/IDE shortcut · Don't use shortcuts |
| 8 | Notifications mostly look like? | Mostly Slack · Mostly email · Calendar reminders · Industry-app alerts · Almost nothing — I disable · Phone (texts/calls) · Mixed mess |
| 9 | App you opened today and immediately closed? | Email · Slack · LinkedIn/Twitter · An AI tool · A spreadsheet · Calendar · Didn't happen |
| 10 | When you save a note for later, where? | Notion/Obsidian · Apple Notes/etc. · Draft email to self · Slack to self · Physical notebook · Browser bookmark · I forget where |
| 11 | If your AI sent ONE message right now, you'd want? | "Here's what you missed yesterday" · "Draft of what you were going to write" · "What changed in [system]" · "Follow up with [person]" · "2-line summary of [thing]" · "Stop, mistake incoming" · "Answer to what you're about to Google" |
| 12 | Your relationship with new tools? | Always trying latest · Adopt slowly, stick · Only switch when forced · Rather build my own · Want company to set up |

### Walkthrough

**ACCA picks**: Q1=4–10 · Q2=Excel + Email + Browser + Industry app · Q3=Reference docs · Q4=.xlsx · Q5=Routine · Q6=Internal docs · Q7=Save · Q8=Mostly email · Q9=Email · Q10=Draft email to self · Q11=2-line summary · Q12=Adopt slowly

**→ Profile**: heavy spreadsheet user, doc-heavy reference work, email-driven communication, low AI risk-tolerance, summarization-hungry. **Industry inferred from file extension + dock pattern alone.**

**SWE picks**: Q1=10–30 · Q2=Code editor + Browser + Slack + ChatGPT · Q3=Logs/dashboards · Q4=.py/.js/.sql · Q5=Half meetings, half deep · Q6=ChatGPT/Claude · Q7=Vim/IDE shortcut · Q8=Mostly Slack · Q9=An AI tool · Q10=Notion/Obsidian · Q11=What changed in [system] · Q12=Always trying latest

**→ Profile**: power user, code-native, high AI maturity, evaluator-mindset (recently tried+closed an AI tool), wants observability over their systems. **Recommend differently from ACCA — more specialized, dev-tooling, less hand-holding.**

**Doctor picks**: Q1=1–3 · Q2=Email + Industry app + Calendar · Q3=I don't use one · Q4=Industry-specific · Q5=Reactive · Q6=Ask colleague · Q7=Don't use shortcuts · Q8=Industry-app alerts · Q9=Didn't happen · Q10=Physical notebook · Q11=Follow up with [person] · Q12=Only switch when forced

**→ Profile**: low digital fluency for non-clinical tools, EHR-bound, paper still in workflow, conservative, relationship-driven. **Aggressive paradigm filter: don't recommend anything power-user.**

---

## Variant C — "Forced-choice / trade-offs"

**Premise**: every question is "would you rather." Reveals values, paradigm, tolerance more sharply than describing tasks.

| # | Question | Options |
|---|---|---|
| 1 | Which describes your work? | Same process every cycle · Every project is different |
| 2 | What frustrates more? | Powerful tool, 30-min learning curve · Easy tool, limited |
| 3 | Pick what you'd rather do for an hour | Write a long doc from scratch · Edit someone else's draft · Talk to a person about it · Work with numbers about it |
| 4 | One must go | Tool that's fast but sometimes wrong · Tool that's slow but always correct |
| 5 | Worst part of your day | Repetitive tasks · Decisions with incomplete info · Coordinating with people · Context switching · Not knowing the priority |
| 6 | Better Tuesday | Clean inbox at 5pm · Shipped thing at 5pm · Finalized number at 5pm · Patient/client thanked you · Doc everyone agreed on |
| 7 | Your AI archetype | Faster typist (writes for me) · Better Google (finds for me) · Second brain (remembers for me) · First-pass reviewer (catches mistakes) · Summarizer · Coordinator (handles people) |
| 8 | Worst kind of AI wrong? | Confident but factually wrong · Vague/wishy-washy · Slow · Wrong format · Generic / misses my context |
| 9 | Trade you actually want | 5% less accuracy for 50% more speed · 5% less speed for 50% more accuracy · Both — I'll pay · Neither — just work in my flow |
| 10 | Better tool outcome | Does task while I'm away · Coaches me through it · Shows a faster way · Does boring 80%, I do 20% |
| 11 | Where does AI fit your week? | First thing (plan day) · During tasks · Meeting time (capture) · End of day (summary) · Fridays (wrap week) · Whenever I'm stuck |
| 12 | "This tool will change how you work" → you feel | Excited · Skeptical · Curious for 5 min · Resistant · Tired (heard it before) |

### Walkthrough

**ACCA picks**: Q1=Same process · Q2=Easy tool, limited · Q3=Numbers · Q4=Slow but correct · Q5=Repetitive tasks · Q6=Finalized number · Q7=First-pass reviewer · Q8=Confident but wrong · Q9=Less speed, more accuracy · Q10=Boring 80%, I do 20% · Q11=End of day · Q12=Skeptical

**→ Profile**: accuracy-first, process-driven, doesn't trust AI auto-pilot, wants reviewer not writer. **Major filter: never recommend autonomous-action tools; recommend "drafts + you check."**

**SWE picks**: Q1=Every project different · Q2=Powerful, 30-min curve · Q3=Edit someone's draft · Q4=Fast, sometimes wrong · Q5=Context switching · Q6=Shipped thing · Q7=Faster typist · Q8=Generic/misses context · Q9=Less accuracy for speed · Q10=Coaches me · Q11=During tasks · Q12=Curious for 5 min

**→ Profile**: speed-over-accuracy, learns fast, wants in-flow assistance not autopilot, allergic to generic. **Recommend: tools with strong context-injection (project-aware), fast iteration loops.**

**Doctor picks**: Q1=Same process · Q2=Easy tool, limited · Q3=Talk to person · Q4=Slow but correct · Q5=Coordinating with people · Q6=Patient thanked you · Q7=Second brain · Q8=Confident but wrong · Q9=Just work in my flow · Q10=Boring 80%, I do 20% · Q11=Meeting time · Q12=Tired

**→ Profile**: relationship-driven, accuracy-critical, communication-bottlenecked, AI-fatigue, wants in-conversation help. **Recommend: ambient scribe + dictation tools only; nothing autonomous, nothing requiring context-feeding.**

---

## My recommendation

**Variant B ("Picture your screen") wins** for Mesh's first version, because:

1. **Picks fingerprint industry without saying so.** File extension + dock + monitor combo alone differentiates ACCA / SWE / Doctor in 3 questions.
2. **Concrete > abstract.** "How many tabs are open?" gets a real answer; "what's your work style?" gets noise.
3. **Naturally MCQ.** Almost every question has a tight option set.

**Add 2 questions from Variant C** as paradigm-locks (Q9 trade and Q12 attitude — they reveal more in 2 questions than 5 lifestyle questions can).

**Skip Variant A's first 3 questions** — they're too literal ("first thing you open"). Variant B's "tabs open + dock + file extension" beat them on signal-density.

### Suggested final V1 (10 from B + 2 from C)

B-Q1, B-Q2, B-Q4, B-Q5, B-Q7, B-Q8, B-Q9, B-Q10, B-Q11, B-Q12 + C-Q9 (trade-off) + C-Q12 (attitude). Drops B-Q3 (monitor — too narrow) and B-Q6 (Google vs ChatGPT — covered by Q11).

Want me to lock this version and build the validation scenarios on it, or iterate on questions more first?
