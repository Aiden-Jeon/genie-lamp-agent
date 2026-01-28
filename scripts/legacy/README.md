# Legacy Scripts

⚠️ **DEPRECATED** - These scripts are deprecated and kept only for backward compatibility.

## Migration Guide

These legacy scripts have been replaced by the unified `genie.py` CLI. Please migrate to the new interface:

### Old Workflow → New Workflow

#### Full Pipeline
**Old:**
```bash
python scripts/legacy/generate_config_with_direct_benchmarks.py --model databricks-gpt-5-2 --input-data data/demo.md
python scripts/legacy/validate_tables.py
python scripts/legacy/create_genie_space.py
```

**New:**
```bash
python genie.py create --requirements data/demo.md
```

#### Generate Only
**Old:**
```bash
python scripts/legacy/main.py --model databricks-gpt-5-2 --input-data data/demo.md
```

**New:**
```bash
python genie.py generate --requirements data/demo.md
```

#### Validate Only
**Old:**
```bash
python scripts/legacy/validate_tables.py
```

**New:**
```bash
python genie.py validate
```

#### Deploy Only
**Old:**
```bash
python scripts/legacy/create_genie_space.py
```

**New:**
```bash
python genie.py deploy
```

## Why Migrate?

The new `genie.py` CLI provides:
- ✅ **Simpler** - One command instead of three
- ✅ **Better UX** - Progress indicators and clear error messages
- ✅ **Error Handling** - Automatic validation and recovery
- ✅ **Consistency** - Unified interface and options
- ✅ **Maintainability** - Single source of truth

## Legacy Scripts

- `main.py` - Basic config generator (replaced by `genie.py generate`)
- `generate_config_with_direct_benchmarks.py` - Full generator (replaced by `genie.py generate`)
- `validate_tables.py` - Table validator (replaced by `genie.py validate`)
- `create_genie_space.py` - Space creator (replaced by `genie.py deploy`)
- `create_genie_space_workflow.sh` - Automated workflow (replaced by `genie.py create`)
- `update_benchmarks.py` - Benchmark updater (no longer needed - `genie.py generate` extracts 100% of benchmarks)
- `fix_benchmarks.sh` - Benchmark fix wrapper (no longer needed)

## Support

These legacy scripts will remain functional but will not receive new features. They may be removed in a future major version.

For issues or questions, please use the new `genie.py` CLI and refer to the main [README.md](../../README.md).
