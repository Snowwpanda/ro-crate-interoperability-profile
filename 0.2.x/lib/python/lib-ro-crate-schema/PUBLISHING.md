# Publishing Guide for lib-ro-crate-schema

This guide walks through the process of publishing this package to PyPI (Python Package Index).

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - Test PyPI: https://test.pypi.org/account/register/
   - Production PyPI: https://pypi.org/account/register/

2. **API Tokens**: Generate API tokens for authentication:
   - Test PyPI: https://test.pypi.org/manage/account/token/
   - Production PyPI: https://pypi.org/manage/account/token/
   
   Save these tokens securely - you'll use them instead of passwords.

3. **Install Build Tools**:
   ```bash
   pip install --upgrade build twine
   ```

## Pre-Publication Checklist

Before publishing, ensure:

- [ ] Version number updated in `pyproject.toml` (follow [Semantic Versioning](https://semver.org/))
- [ ] `README.md` is up-to-date and renders correctly
- [ ] All tests pass: `python run_all_tests.py`
- [ ] `LICENSE` file is present
- [ ] Dependencies in `pyproject.toml` are correct and use appropriate version constraints
- [ ] Author information is correct
- [ ] Repository URLs are correct

## Building the Package

1. **Clean Previous Builds**:
   ```bash
   # Remove old build artifacts
   rm -rf dist/ build/ *.egg-info
   ```

2. **Build Distribution Files**:
   ```bash
   python -m build
   ```

   This creates two files in the `dist/` directory:
   - `.tar.gz` - Source distribution
   - `.whl` - Wheel (binary distribution)

3. **Verify the Build**:
   ```bash
   # List generated files
   ls dist/
   
   # Check package contents
   tar -tzf dist/lib-ro-crate-schema-*.tar.gz
   ```

## Testing on Test PyPI (Recommended First Step)

Always test your package on Test PyPI before publishing to production:

1. **Upload to Test PyPI**:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```
   
   When prompted:
   - Username: `__token__`
   - Password: Your Test PyPI API token (including the `pypi-` prefix)

2. **Test Installation**:
   ```bash
   # Create a fresh virtual environment
   python -m venv test_env
   source test_env/bin/activate  # On Windows: test_env\Scripts\activate
   
   # Install from Test PyPI
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lib-ro-crate-schema
   
   # Test the installation
   python -c "from lib_ro_crate_schema import SchemaFacade, ro_crate_schema; print('Import successful!')"
   ```

3. **Run Your Examples**:
   ```bash
   # Copy your examples to the test environment and run them
   python examples/decorator_example.py
   ```

## Publishing to Production PyPI

Once you've verified everything works on Test PyPI:

1. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```
   
   When prompted:
   - Username: `__token__`
   - Password: Your PyPI API token (including the `pypi-` prefix)

2. **Verify on PyPI**:
   - Visit: https://pypi.org/project/lib-ro-crate-schema/
   - Check that the README renders correctly
   - Verify all links work

3. **Test Installation**:
   ```bash
   # In a fresh environment
   pip install lib-ro-crate-schema
   python -c "from lib_ro_crate_schema import SchemaFacade; print('Success!')"
   ```

## Using GitHub Actions (Automated Publishing)

For automated publishing on release, create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
        working-directory: 0.2.x/lib/python/lib-ro-crate-schema
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: python -m twine upload dist/*
        working-directory: 0.2.x/lib/python/lib-ro-crate-schema
```

Then add your PyPI API token as a GitHub secret named `PYPI_API_TOKEN`.

## Post-Publication

1. **Tag the Release**:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

2. **Create GitHub Release**:
   - Go to your repository's Releases page
   - Create a new release from the tag
   - Add release notes describing changes

3. **Update Documentation**:
   - Update any documentation that references installation
   - Announce the release (if applicable)

## Version Management

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): Add functionality (backwards-compatible)
- **PATCH** (0.0.X): Bug fixes (backwards-compatible)

Update version in:
1. `pyproject.toml` - `version = "X.Y.Z"`
2. `src/lib_ro_crate_schema/__init__.py` - `__version__ = "X.Y.Z"`

## Troubleshooting

### "File already exists" Error
- You cannot upload the same version twice to PyPI
- Increment the version number in `pyproject.toml` and rebuild

### Import Errors After Installation
- Check that `__init__.py` files properly export all public APIs
- Verify package structure with: `python -m pip show -f lib-ro-crate-schema`

### README Not Rendering
- Validate Markdown: Use online tools or VS Code preview
- Ensure `readme = "README.md"` in `pyproject.toml`
- Check that README.md is in the same directory as pyproject.toml

### Missing Dependencies
- Ensure all dependencies are listed in `pyproject.toml`
- Test in a clean virtual environment

## Security Best Practices

1. **Never commit API tokens** to version control
2. **Use API tokens** instead of passwords (more secure, can be revoked)
3. **Limit token scope** to just uploads if possible
4. **Rotate tokens** periodically
5. **Use GitHub Secrets** for CI/CD automation

## Resources

- PyPI Help: https://pypi.org/help/
- Python Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/
- Semantic Versioning: https://semver.org/

## Quick Reference Commands

```bash
# Clean build
rm -rf dist/ build/ *.egg-info

# Build package
python -m build

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lib-ro-crate-schema  # Test PyPI
pip install lib-ro-crate-schema  # Production PyPI
```
