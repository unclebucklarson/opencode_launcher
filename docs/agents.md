# Agent Templates

Agents give your OpenCode instances a personality and purpose. Instead of a blank-slate AI, you get a specialized persona tuned for the task at hand.

---

### Table of Contents

- [What Are Agent Templates?](#what-are-agent-templates)
- [Built-in Agents](#built-in-agents)
- [Agent File Format](#agent-file-format)
- [Creating Custom Agents](#creating-custom-agents)
- [Using Agents](#using-agents)
- [Tips for Good Agents](#tips-for-good-agents)

---

### What Are Agent Templates?

An agent template is a Markdown file with YAML frontmatter that defines:

1. **Metadata** — Name, description, and temperature setting
2. **System prompt** — The behavioral instructions for the AI

When you launch an instance with an agent, the template file is passed to OpenCode via the `--agent` flag. OpenCode uses it to configure the AI's behavior for that session.

Agent templates live in:
```
~/.config/opencode-launcher/agents/
```

---

### Built-in Agents

OpenCode Launcher ships with 5 built-in agent templates:

#### `analyst` — Data Analyst
- **Temperature:** 0.5
- **Best for:** Data exploration, analysis, insights extraction, reporting
- **Style:** Methodical, evidence-based, asks clarifying questions before diving in

#### `coding` — Software Developer
- **Temperature:** 0.4
- **Best for:** Writing code, architecture design, refactoring, debugging
- **Style:** Clean code advocate, follows SOLID principles, provides runnable code

#### `general` — General Assistant
- **Temperature:** 0.5
- **Best for:** Broad tasks, brainstorming, ad-hoc requests
- **Style:** Adaptable, conversational, handles anything you throw at it

#### `qa` — QA Engineer
- **Temperature:** 0.3
- **Best for:** Testing, bug hunting, edge case identification, validation
- **Style:** Thorough, skeptical (in a good way), categorizes issues by severity

#### `technical-writer` — Technical Writer
- **Temperature:** 0.4
- **Best for:** Documentation, READMEs, guides, API docs
- **Style:** Clear, structured, example-heavy, audience-aware

---

### Agent File Format

Agent files are Markdown with YAML frontmatter:

```markdown
---
name: Display Name Here
description: One-line description of what this agent does
temperature: 0.4
---

The rest of the file is the system prompt.
It can use full Markdown formatting.

## Sections Are Fine

- Bullet points work
- Code blocks work
- Everything Markdown supports works
```

#### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name shown in agent listings |
| `description` | string | Yes | One-line description shown in selection menus |
| `temperature` | float | No | Model temperature (0.0–1.0). Lower = more focused, higher = more creative. Default: 0.5 |

#### System Prompt (Body)

The body of the Markdown file (after the frontmatter) is the system prompt. This is where you define:

- The agent's role and expertise
- Working style and approach
- Output format preferences
- Rules and constraints
- Any special instructions

---

### Creating Custom Agents

Creating a custom agent is as simple as dropping a `.md` file into the agents directory.

#### Step 1: Create the File

```bash
vi ~/.config/opencode-launcher/agents/devops.md
```

#### Step 2: Write the Template

```markdown
---
name: DevOps Engineer
description: Infrastructure, CI/CD, and deployment specialist
temperature: 0.3
---

You are a senior DevOps engineer specializing in:

## Core Expertise
- Infrastructure as Code (Terraform, Pulumi, CloudFormation)
- CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- Container orchestration (Kubernetes, Docker Compose)
- Cloud platforms (AWS, GCP, Azure)
- Monitoring and observability (Prometheus, Grafana, Datadog)

## Working Style
- Always consider security implications
- Prefer declarative over imperative configurations
- Explain trade-offs between approaches
- Include rollback strategies
- Think about cost optimization

## Output Format
- Provide complete, copy-pasteable config files
- Include comments explaining non-obvious settings
- Note any prerequisites or dependencies
- Suggest monitoring/alerting for critical components
```

#### Step 3: Verify

```bash
oc list-agents
```

Your new agent should appear in the list immediately — no restart needed.

#### Step 4: Use It

```bash
oc launch -a devops -d ~/infra/kubernetes
```

---

### Using Agents

#### In Interactive Mode

```bash
oc launch
# ... wizard steps ...
# ? Select agent template:
# ❯ analyst
#   coding
#   devops          ← your custom agent!
#   general
#   qa
#   technical-writer
#   (none)
```

#### Via CLI Flags

```bash
oc launch -m qwen2.5-coder:32b -d ~/project -a coding
```

The `-a` / `--agent` flag takes the **slug** — the filename without the `.md` extension.

#### Via Config File

```json
{
  "model": "qwen2.5-coder:32b",
  "directory": "~/project",
  "agent": "coding"
}
```

#### Without an Agent

If you don't want an agent, select `(none)` in the wizard or simply omit the `-a` flag. OpenCode will launch with its default behavior.

---

### Tips for Good Agents

#### 1. Be Specific About the Role

❌ *"You are helpful."*
✅ *"You are a senior backend engineer specializing in Python microservices with 10 years of experience in distributed systems."*

#### 2. Define the Working Style

Tell the agent *how* to approach problems, not just *what* to do:
- Should it ask clarifying questions first?
- Should it explain its reasoning?
- Should it provide alternatives?

#### 3. Specify Output Format

Be explicit about what you want:
- Complete, runnable code vs. snippets?
- Markdown formatting?
- Structured sections?

#### 4. Set Appropriate Temperature

| Temperature | Best For |
|-------------|----------|
| 0.1–0.3 | Precise tasks: code generation, testing, analysis |
| 0.4–0.6 | Balanced tasks: documentation, general coding |
| 0.7–1.0 | Creative tasks: brainstorming, content writing |

#### 5. Use Markdown Structure

Organize the prompt with headers, bullet points, and sections. It makes the system prompt clearer for both you and the model.

#### 6. Test and Iterate

Launch with the agent, try a few tasks, and refine the prompt based on results. Agents are just text files — edit and relaunch.

---

### Example: Full Custom Agent

Here's a complete example of a security-focused agent:

```markdown
---
name: Security Auditor
description: Application security review and vulnerability assessment
temperature: 0.2
---

You are a senior application security engineer performing code review.

## Primary Objectives
- Identify security vulnerabilities in code
- Assess risk severity (Critical, High, Medium, Low, Info)
- Provide actionable remediation steps
- Reference relevant CWE/OWASP categories

## Review Checklist
- Injection flaws (SQL, XSS, Command, LDAP)
- Authentication and session management
- Access control and authorization
- Cryptographic failures
- Security misconfigurations
- Vulnerable dependencies
- Data exposure risks
- Input validation gaps

## Output Format
For each finding:
1. **Title**: Brief description
2. **Severity**: Critical/High/Medium/Low/Info
3. **Location**: File and line reference
4. **Description**: What's wrong and why it matters
5. **Remediation**: How to fix it with code examples
6. **Reference**: CWE or OWASP link

## Rules
- Never suggest disabling security controls
- Always consider the principle of least privilege
- Flag hardcoded secrets immediately
- Consider both current exploitability and potential future risk
```

---

### Next Steps

- 🔧 [Workflows](workflows.md) — See agents in action with real usage patterns
- 📖 [Command Reference](command-reference.md) — All the flags for launching with agents
- ⚙️ [Configuration](configuration.md) — Set agents in config files
