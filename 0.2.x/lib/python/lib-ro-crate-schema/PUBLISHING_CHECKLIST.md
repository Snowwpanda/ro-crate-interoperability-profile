# PyPI Publishing Checklist

Use this checklist when you're ready to publish to PyPI.

## Pre-Publishing ✅

- [ ] All tests pass: `python run_all_tests.py`
- [ ] Examples run successfully: `python examples/decorator_example.py`
- [ ] Version updated in:
  - [ ] `pyproject.toml` (line 3: `version = "X.Y.Z"`)
  - [ ] `src/lib_ro_crate_schema/__init__.py` (line 25: `__version__ = "X.Y.Z"`)
  - [ ] `src/lib_ro_crate_schema/crate/__init__.py` (line 4: `__version__ = "X.Y.Z"`)
- [ ] Changes committed to git
- [ ] Git tag created: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`

## Build Package ✅

```bash
cd "c:\git\eln_interoperability\ro-crate-interoperability-profile\0.2.x\lib\python\lib-ro-crate-schema"

# Clean old builds
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# Build
python -m build

# Verify
python -m twine check dist/*
```

- [ ] Build completed without errors
- [ ] Twine check passed

## Test on Test PyPI ✅

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: `[Your Test PyPI API token]`

- [ ] Uploaded successfully
- [ ] Check the page: https://test.pypi.org/project/lib-ro-crate-schema/

### Test Installation

```bash
# Create test environment
python -m venv test_env
test_env\Scripts\activate

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lib-ro-crate-schema

# Test import
python -c "from lib_ro_crate_schema import SchemaFacade, ro_crate_schema; print('✅ Import successful!')"
```

- [ ] Installed without errors
- [ ] Import works correctly
- [ ] Basic functionality works

## Publish to PyPI ✅

**⚠️ This cannot be undone! Once published, you cannot upload the same version again.**

```bash
# Upload to production PyPI
python -m twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: `[Your PyPI API token]`

- [ ] Uploaded successfully
- [ ] Check the page: https://pypi.org/project/lib-ro-crate-schema/
- [ ] README renders correctly on PyPI

### Verify Installation

```bash
# Fresh environment
python -m venv verify_env
verify_env\Scripts\activate

# Install from PyPI
pip install lib-ro-crate-schema

# Test
python -c "from lib_ro_crate_schema import SchemaFacade; print('✅ Success!')"
```

- [ ] Installed from PyPI successfully
- [ ] All imports work

## Post-Publishing ✅

- [ ] Push git tag: `git push origin vX.Y.Z`
- [ ] Create GitHub release from tag
- [ ] Add release notes to GitHub release
- [ ] Update CHANGELOG (if you have one)
- [ ] Announce release (if applicable)

## Quick Commands

```bash
# All in one - Test PyPI
python -m build && python -m twine check dist/* && python -m twine upload --repository testpypi dist/*

# All in one - Production PyPI
python -m build && python -m twine check dist/* && python -m twine upload dist/*
```

## Need Help?

- **Test PyPI**: https://test.pypi.org/account/register/
- **PyPI**: https://pypi.org/account/register/
- **Full Guide**: See [PUBLISHING.md](PUBLISHING.md)
- **Package Docs**: See [README.md](README.md)

---

**Remember**: 
- Always test on Test PyPI first!
- You cannot reupload the same version to PyPI
- Keep your API tokens secure
