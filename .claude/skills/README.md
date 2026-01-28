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

## Installing Skills

### Option 1: Symlink to Claude Code skills directory (Recommended)

This makes the skills available globally in Claude Code:

```bash
# Create symlink for genie-commit
ln -s "$(pwd)/.claude/skills/genie-commit" ~/.codex/skills/genie-commit

# Verify
ls -la ~/.codex/skills/genie-commit
```

### Option 2: Copy to Claude Code skills directory

```bash
# Copy the skill
cp -r .claude/skills/genie-commit ~/.codex/skills/

# Verify
ls -la ~/.codex/skills/genie-commit
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
