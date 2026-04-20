# /lay-of-the-land

Analyze one or more GitHub repositories against the Lay of the Land Brief (Section A) and produce a structured output folder with per-repo reports, structured JSON, and cross-repo synthesis.

## Arguments

The user provides one or more space-separated GitHub repository URLs as arguments: `$ARGUMENTS`

## Workflow

Execute the following phases in order. If any phase fails critically, report the error and stop.

### Phase 1: Setup

1. Parse `$ARGUMENTS` into a list of URLs. Each must match the pattern `https://github.com/{owner}/{repo}` (with optional trailing slash or `.git`). Warn and skip any URL that doesn't match. If no valid URLs remain, abort with an error message.

2. Verify GitHub CLI authentication by running:
   ```bash
   gh auth status
   ```
   If this fails, abort with: "GitHub CLI is not authenticated. Run `gh auth login` first."

3. Set the run date:
   ```bash
   date +%Y-%m-%d
   ```

4. Create the output directory structure:
   ```bash
   mkdir -p lotl-{DATE}/analysis
   ```
   If analyzing 2+ repos, also create:
   ```bash
   mkdir -p lotl-{DATE}/cross-repo
   ```

5. Write `lotl-{DATE}/manifest.json` with:
   ```json
   {
     "run_date": "{DATE}",
     "timestamp": "{ISO-8601 timestamp}",
     "repos": ["{url1}", "{url2}", ...],
     "repo_count": N,
     "tool_version": "1.0.0"
   }
   ```

### Phase 2: Clone

For each valid repo URL:

1. Extract `{owner}/{repo}` from the URL.
2. Clone to a temporary directory:
   ```bash
   TMPDIR=$(mktemp -d)
   gh repo clone {owner}/{repo} "$TMPDIR/{repo}" -- --depth 100
   ```
3. Record the default branch and HEAD commit SHA:
   ```bash
   cd "$TMPDIR/{repo}"
   git rev-parse --abbrev-ref HEAD
   git rev-parse HEAD
   ```
4. Store `clone_path`, `default_branch`, and `commit_sha` for use in Phase 3.

If a clone fails (404, private repo, network error), warn the user, skip that repo, and continue. If ALL repos fail to clone, abort with an error.

### Phase 3: Per-Repo Analysis

For each successfully cloned repo, run the two analysis agents. You MUST launch them in parallel using the Task tool with `run_in_background: true` to analyze repos concurrently when there are multiple repos.

For each repo, launch these two agents:

**Agent 1: stack-analyzer**
Use the Task tool with `subagent_type: "Explore"` and provide:
- The clone path
- The repo name and URL
- Instruct it to follow the `.claude/agents/stack-analyzer.md` instructions
- It must return a JSON object matching the `developer_tools` schema

**Agent 2: ai-specs-analyzer**
Use the Task tool with `subagent_type: "Explore"` and provide:
- The clone path
- The repo name and URL
- Instruct it to follow the `.claude/agents/ai-specs-analyzer.md` instructions
- It must return a JSON object matching the `ai_capabilities` and `specs_documentation` schemas

### Phase 4: Per-Repo Reports

For each repo, after both agents complete:

1. Create the repo analysis directory:
   ```bash
   mkdir -p lotl-{DATE}/analysis/{repo-name}
   ```

2. Write `data.json` — merge the two agent outputs into the full schema:
   ```json
   {
     "metadata": {
       "repo_url": "https://github.com/{owner}/{repo}",
       "repo_name": "{repo}",
       "default_branch": "{branch}",
       "analyzed_at": "{ISO-8601}",
       "commit_sha": "{sha}"
     },
     "developer_tools": { ... },
     "ai_capabilities": { ... },
     "specs_documentation": { ... }
   }
   ```

3. Write `summary.md` — a human-readable report structured as:

   ```markdown
   # {repo-name} — Lay of the Land Analysis

   **Repository**: {url}
   **Branch**: {default_branch} @ `{short_sha}`
   **Analyzed**: {DATE}

   ---

   ## 1. Developer Tools & Platform Stack

   ### 1.1 Development Environment
   - **Languages**: {list or "None detected"}
   - **Package Managers**: {list or "None detected"}
   - **Formatting & Linting**: {list or "None detected"}

   ### 1.2 Code Quality & Testing
   - **Test Frameworks**: {list or "None detected"}
   - **Coverage Tools**: {list or "None detected"}
   - **Static Analysis**: {list or "None detected"}

   ### 1.3 Source Control & Collaboration
   - **Platform**: {platform}
   - **Repo Strategy**: {mono/multi/single}
   - **Branching Strategy**: {strategy or "Not determinable"}
   - **PR Policies**: {details or "Not determinable"}

   ### 1.4 CI/CD & Deployment
   - **CI/CD Tools**: {list or "None detected"}
   - **Feature Flags**: {list or "None detected"}
   - **A/B Testing**: {list or "None detected"}

   ### 1.5 Infrastructure & Platform
   - **Cloud Providers**: {list or "None detected"}
   - **Containerization**: {list or "None detected"}
   - **Serverless**: {list or "None detected"}
   - **IaC Tools**: {list or "None detected"}
   - **Config Management**: {list or "None detected"}
   - **Environments**: {list or "Not determinable"}

   ### 1.6 Observability & Reliability
   - **Logging**: {list or "None detected"}
   - **Metrics & Monitoring**: {list or "None detected"}
   - **Error Tracking**: {list or "None detected"}

   ### 1.7 Data & Messaging
   - **ETL/ELT**: {list or "None detected"}
   - **Data Orchestration**: {list or "None detected"}
   - **Message Queues**: {list or "None detected"}
   - **Task Queues**: {list or "None detected"}
   - **Job Schedulers**: {list or "None detected"}
   - **Cron Schedulers**: {list or "None detected"}
   - **Background Workers**: {list or "None detected"}

   ---

   ## 2. AI-First & ML Engineering Capabilities

   ### 2.1 AI Development Stack
   - **LLM Orchestration**: {list or "None detected"}
   - **LLM Models**: {list or "None detected"}
   - **Prompt Management**: {list or "None detected"}
   - **Vector Databases**: {list or "None detected"}
   - **Agent Frameworks**: {list or "None detected"}
   - **State Machines**: {list or "None detected"}
   - **MCP Tools**: {list or "None detected"}
   - **Agent Architecture Type**: {type or "None detected"}

   ### 2.2 Memory Architecture
   - **Short-term Memory**: {details or "None detected"}
   - **Long-term Memory**: {details or "None detected"}
   - **Session-based Memory**: {details or "None detected"}
   - **Project-based Memory**: {details or "None detected"}
   - **Knowledge Graphs**: {details or "None detected"}

   ---

   ## 3. Specifications & Documentation

   ### 3.1 Specification Presence
   - **Spec Directories**: {list or "None found"}
   - **Product Requirements**: {details or "None found"}
   - **Architecture Docs**: {details or "None found"}

   ### 3.2 Specs-Driven Development
   - **Specs-First Workflow**: {evidence or "No evidence found"}
   - **Spec-Driven PR Patterns**: {evidence or "No evidence found"}

   ### 3.3 Process & Quality Metrics
   - **Hotfix Rate**: {rate or "Not calculable"}
   - **Rollback Rate**: {rate or "Not calculable"}
   - **PR Cycle Time**: {time or "Not available"}
   - **Documentation Coverage**: {ratio or "Not calculable"}
   ```

### Phase 5: Cross-Repo Synthesis (only if 2+ repos analyzed)

Run the cross-repo-synthesizer agent via the Task tool. Provide it:
- The paths to all per-repo `data.json` files
- The list of repo names

The agent should follow `.claude/agents/cross-repo-synthesizer.md` instructions and produce:

1. `lotl-{DATE}/cross-repo/architectural-summary.md` — narrative cross-cutting analysis
2. `lotl-{DATE}/cross-repo/comparison-matrix.md` — side-by-side markdown table

### Phase 6: Top-Level Report

1. Write `lotl-{DATE}/report.json`:
   ```json
   {
     "run_date": "{DATE}",
     "repos_analyzed": N,
     "repos_failed": M,
     "repos": {
       "{repo-name-1}": { ...full data.json contents... },
       "{repo-name-2}": { ...full data.json contents... }
     },
     "cross_repo_summary": {
       "shared_technologies": [...],
       "divergent_technologies": [...],
       "overall_maturity": "..."
     }
   }
   ```

2. Write `lotl-{DATE}/report.md`:
   ```markdown
   # Lay of the Land — Executive Summary

   **Date**: {DATE}
   **Repos Analyzed**: {N}

   ---

   ## Overview

   {2-3 paragraph executive summary of key findings across all repos}

   ---

   ## Per-Repo Reports

   | Repo | Languages | CI/CD | AI Stack | Report |
   |------|-----------|-------|----------|--------|
   | {name} | {langs} | {ci tools} | {ai tools} | [View](analysis/{name}/summary.md) |

   ---

   {If cross-repo analysis exists:}
   ## Cross-Repo Analysis

   - [Architectural Summary](cross-repo/architectural-summary.md)
   - [Comparison Matrix](cross-repo/comparison-matrix.md)
   ```

### Phase 7: Cleanup

1. Remove all temporary clone directories:
   ```bash
   rm -rf "$TMPDIR"
   ```

2. Print a summary to the console:
   ```
   Lay of the Land analysis complete.
   Output: lotl-{DATE}/
   Repos analyzed: {N}
   Repos skipped: {M}
   Report: lotl-{DATE}/report.md
   ```

## Error Handling

| Error | Action |
|-------|--------|
| Invalid URL format | Warn and skip, continue with valid URLs |
| `gh` not authenticated | Abort with `gh auth login` instructions |
| Clone fails (404, private) | Warn, skip repo, continue with others |
| GitHub API rate limit | Skip PR metrics, note in report |
| No repos succeed | Abort with error message |
| Agent returns malformed data | Use empty defaults for that section, note in report |
