# Claude Code Skills for Genie Lamp Agent

This directory contains custom Claude Code skills for the Genie Lamp Agent project.

## What are Skills?

Skills are modular packages that extend Claude Code's capabilities by providing:
- Specialized workflows for specific tasks
- Project-specific knowledge and best practices
- Automated procedures with validation
- Bundled scripts and references

## Available Skills

### genie-commit

Automated git commit workflow with testing and validation.

**Triggers:** When you ask to "commit changes", "create a commit", or "save to git"

**Features:**
- Runs `.venv/bin/python -m pytest tests/ -v` before committing
- Analyzes changes to suggest commit type (feat/fix/refactor/docs/test)
- Follows conventional commit message format
- Checks for sensitive files (.env, tokens)
- Includes Co-Authored-By attribution for Claude

**Example Usage:**
```
User: "commit these changes"

Claude will:
1. Check git status and diff
2. Run full test suite
3. Analyze changes and classify commit type
4. Craft appropriate commit message
5. Stage files explicitly
6. Create commit with proper formatting
```

### genie-deploy

Automated Genie space deployment from real_requirements/inputs with automatic catalog replacement.

**Triggers:** When you ask to "deploy genie", "create a genie space from real requirements", or "run automated deployment"

**Features:**
- Parses documents from `real_requirements/inputs/` directory
- Generates Genie space configuration using LLM
- Validates tables against Unity Catalog
- **Automatically replaces** failed catalog.schema with `sandbox.agent_poc`
- Retries validation up to 3 times
- Deploys to Databricks workspace

**Example Usage:**
```
User: "deploy genie from real requirements"

Claude will:
1. Parse PDFs/markdown from real_requirements/inputs/
2. Generate structured requirements
3. Create Genie configuration
4. Validate tables (auto-replace with sandbox.agent_poc)
5. Deploy the Genie space
6. Return space ID and URL
```

**Script:** `scripts/auto_deploy.py`

**Key Configuration:**
- Input: `real_requirements/inputs/` directory (requirements documents)
- Benchmarks: `real_requirements/benchmarks/` directory (optional)
- Parsed output: `data/parsed.md`
- Config output: `output/genie_space_config.json`
- Result output: `output/genie_space_result.json`
- Auto-replacement: `sandbox.agent_poc`

**Troubleshooting:**
If deployment fails with `INTERNAL_ERROR`:
- Check for special characters (backticks, complex parentheses) in space_name, description, or purpose
- Clean metadata: Use simple names without special formatting
- Verify table names match Unity Catalog (e.g., `steam_app_id` → `steam_apps`)
- Test with minimal config first, then incrementally add components

See `genie-deploy/skill.md` for detailed troubleshooting steps.

### deploy-app

Deploy the Genie Lamp Agent Databricks app using Asset Bundles.

**Triggers:** When you ask to "deploy the app", "deploy genie-lamp-agent", "update the app", or "publish the app"

**Features:**
- Automated Databricks app deployment using Asset Bundles
- Support for both initial deployment (first-time) and update deployment
- Automatic handling of bundle deploy, app start, and app deploy commands
- Environment-specific deployments (dev, prod)
- Working directory support for nested bundle configs
- Pre-deployment validation (secrets, config files)

**Example Usage:**
```
User: "deploy the app to dev"

Claude will:
1. Ask for deployment type (initial or update)
2. Confirm source code path
3. Change to app/ directory
4. Run databricks bundle deploy
5. Start app (if initial) or skip (if update)
6. Deploy app code
7. Provide access instructions
```

**Script:** `.claude/skills/deploy-app/scripts/deploy_app.py`

**Project Configuration:**
- Bundle Name: `genie-lamp-agent`
- App Resource Name: `genie_lamp_app`
- Working Directory: `app/`
- Environments: `dev` (default), `prod`
- Source Code Path Pattern: `/Workspace/Users/<username>/.bundle/genie-lamp-agent/<env>/files`

**Prerequisites:**
- Databricks CLI installed and configured
- Secrets configured in `genie-lamp` scope (service-token, sql-warehouse-http-path)
- Frontend built (if deploying after frontend changes): `cd app/frontend && npm run build`

**Common Commands:**
```bash
# Initial deployment to dev
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/user@example.com/.bundle/genie-lamp-agent/dev/files \
  --working-dir app \
  --initial

# Update deployment to dev
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/user@example.com/.bundle/genie-lamp-agent/dev/files \
  --working-dir app \
  --update
```

See `.claude/skills/deploy-app/SKILL.md` for detailed deployment workflows and troubleshooting.

### create-folder

Safely create directories with validation and parent directory creation.

**Triggers:** When you ask to "create folder", "make directory", "mkdir -p", or "ensure folder exists"

**Features:**
- Checks if directory already exists before creation
- Creates parent directories automatically with `-p` flag
- Verifies successful creation
- Handles errors gracefully with clear messages
- Supports single or multiple directory creation

**Example Usage:**
```
User: "create folder if not exists for output"

Claude will:
1. Check if 'output' directory exists
2. Create with mkdir -p if needed
3. Verify creation success
4. Report status to user
```

**Use Cases:**
- Single directory: `mkdir -p data`
- Nested directories: `mkdir -p output/configs/prod`
- Multiple directories: `mkdir -p data benchmarks logs`
- Project structure: `mkdir -p src/api src/models tests/unit`

## Installing Skills

### Option 1: Symlink to Claude Code skills directory (Recommended)

This makes the skills available globally in Claude Code:

```bash
# Create symlinks for all skills
ln -s "$(pwd)/.claude/skills/genie-commit" ~/.codex/skills/genie-commit
ln -s "$(pwd)/.claude/skills/genie-deploy" ~/.codex/skills/genie-deploy
ln -s "$(pwd)/.claude/skills/deploy-app" ~/.codex/skills/deploy-app
ln -s "$(pwd)/.claude/skills/create-folder" ~/.codex/skills/create-folder

# Verify
ls -la ~/.codex/skills/genie-* ~/.codex/skills/deploy-app ~/.codex/skills/create-folder
```

### Option 2: Copy to Claude Code skills directory

```bash
# Copy the skills
cp -r .claude/skills/genie-commit ~/.codex/skills/
cp -r .claude/skills/genie-deploy ~/.codex/skills/
cp -r .claude/skills/deploy-app ~/.codex/skills/
cp -r .claude/skills/create-folder ~/.codex/skills/

# Verify
ls -la ~/.codex/skills/genie-* ~/.codex/skills/deploy-app ~/.codex/skills/create-folder
```

### After Installation

**Restart Claude Code** to load the new skills. The skills will automatically trigger based on their descriptions.

## Creating New Skills

To create additional project-specific skills:

1. Use the skill-creator system skill:
   ```bash
   cd ~/.codex/skills/.system/skill-creator
   python3 scripts/init_skill.py <skill-name> --path $(pwd)/.claude/skills --resources scripts,references
   ```

2. Edit the generated `SKILL.md` with your workflow

3. Add scripts to `scripts/` and references to `references/`

4. Test the skill by symlinking or copying to `~/.codex/skills/`

5. Commit to this repo to version control

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md              # Required: Workflow instructions with YAML frontmatter
├── scripts/              # Optional: Executable Python/Bash scripts
├── references/           # Optional: Documentation loaded as needed
└── assets/               # Optional: Templates, files for output
```

## Best Practices

1. **Keep skills focused** - One skill per major workflow
2. **Be concise** - Skills share context window with conversation
3. **Use references** - Move detailed docs to `references/` to keep SKILL.md lean
4. **Test thoroughly** - Run scripts and test workflows before committing
5. **Document triggers** - Clear description of when skill should activate

## Contributing

When adding new skills:

1. Create skill in `.claude/skills/` directory
2. Test locally by symlinking to `~/.codex/skills/`
3. Update this README with skill description
4. Commit with message: `feat: Add <skill-name> skill for <purpose>`

## References

- [Claude Code Skills Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- Skill creator guide: `~/.codex/skills/.system/skill-creator/SKILL.md`
