# Create Folder If Not Exists

**Description**: Safely create directories with validation and parent directory creation, ensuring proper error handling and user feedback.

**Triggers**: When the user asks to:
- "create folder" or "make directory"
- "create folder if not exists" or "mkdir -p"
- "ensure folder exists" or "setup directory"
- Mentions creating output directories, data directories, or any folder structure

---

## Instructions

When this skill is triggered:

1. **Identify the target directory path**
   - If the user provides a path, use it
   - If no path provided, ask the user for the directory path

2. **Check if directory already exists**
   ```bash
   # Use LS tool to check if directory exists
   ```

3. **Create directory if needed**
   - Use Shell tool with `mkdir -p` to create directory and any missing parent directories
   - The `-p` flag ensures:
     - Parent directories are created automatically
     - No error if directory already exists
   
   ```bash
   mkdir -p /path/to/target/directory
   ```

4. **Verify creation**
   - Use LS tool to confirm the directory was created successfully
   - Report success to the user with the full path

5. **Handle errors gracefully**
   - If permission denied, inform user they need appropriate permissions
   - If path is invalid, explain the issue and suggest corrections
   - If creation fails for other reasons, provide clear error message

## Example Workflow

```
User: "Create folder if not exists for output"

Agent:
1. Check if 'output' directory exists using LS tool
2. If not exists:
   - Run: mkdir -p output
   - Verify with LS tool
   - Report: "Created directory: output"
3. If exists:
   - Report: "Directory already exists: output"
```

## Best Practices

- Always use `mkdir -p` for safe directory creation
- Verify directory creation with LS tool after mkdir
- Provide full absolute paths in confirmation messages
- Handle relative paths by resolving them to absolute paths
- Create parent directories automatically with `-p` flag

## Common Use Cases

### Single Directory
```bash
mkdir -p data
```

### Nested Directories
```bash
mkdir -p output/configs/prod
```

### Multiple Directories
```bash
mkdir -p data benchmarks logs
```

### Project Structure Setup
```bash
mkdir -p src/api src/models src/utils tests/unit tests/integration
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Permission denied | Insufficient permissions | Use sudo or change target location |
| Invalid path | Path contains invalid characters | Clean path and retry |
| Disk full | No space available | Free up space or change location |
| Path is file | Target path is an existing file | Choose different name or remove file |

---

## Notes

- This skill uses Shell tool for `mkdir -p` command
- The `-p` flag makes mkdir idempotent (safe to run multiple times)
- Always verify directory creation success before proceeding with file operations
- Consider adding directories to .gitignore if they contain generated/temporary files