"""
Test that verifies the published package can be installed and used from TestPyPI.

This test creates an isolated environment, installs the package from TestPyPI,
and runs a quickstart-style example to ensure everything works as expected.
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def test_install_from_testpypi():
    """
    Test that the package can be installed from TestPyPI and basic functionality works.
    
    This test:
    1. Creates a temporary virtual environment
    2. Installs the package from TestPyPI
    3. Runs a simple example similar to quickstart
    4. Verifies the output is correct
    """
    
    # Create a temporary directory for our test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"
        
        print(f"\n{'='*60}")
        print("Testing Published Package from TestPyPI")
        print(f"{'='*60}")
        
        # Step 1: Create virtual environment
        print("\n1. Creating virtual environment...")
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to create venv: {result.stderr}"
        print("   ✓ Virtual environment created")
        
        # Determine pip executable path
        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip"
            python_path = venv_path / "Scripts" / "python"
        else:
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"
        
        # Step 2: Install from TestPyPI
        print("\n2. Installing lib-ro-crate-schema from TestPyPI...")
        print("   Note: Package may take a few minutes to be indexed on TestPyPI")
        
        # Try with the specific version (0.2.0 is available on TestPyPI)
        result = subprocess.run(
            [
                str(pip_path),
                "install",
                "--index-url", "https://test.pypi.org/simple/",
                "--extra-index-url", "https://pypi.org/simple/",
                "lib-ro-crate-schema==0.2.0"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"   ✗ Installation failed!")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            assert False, "Failed to install package from TestPyPI"
        
        print("   ✓ Package installed successfully")
        
        # Step 3: Create a test script similar to quickstart
        print("\n3. Creating test script...")
        test_script = venv_path / "test_quickstart.py"
        test_script.write_text("""
# Test script that mimics the quickstart example
from pydantic import BaseModel, Field
from lib_ro_crate_schema.crate.decorators import ro_crate_schema
from lib_ro_crate_schema.crate.schema_facade import SchemaFacade
import json
from pathlib import Path
import tempfile

# Define a schema using decorators
@ro_crate_schema(ontology="https://schema.org/Person")
class Person(BaseModel):
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    email: str = Field(json_schema_extra={"ontology": "https://schema.org/email"})

@ro_crate_schema(ontology="https://schema.org/Organization")
class Organization(BaseModel):
    name: str = Field(json_schema_extra={"ontology": "https://schema.org/name"})
    url: str = Field(json_schema_extra={"ontology": "https://schema.org/url"})

# Create instances
person = Person(name="Alice Researcher", email="alice@example.org")
org = Organization(name="Research Institute", url="https://example.org")

# Create RO-Crate using the actual API
with tempfile.TemporaryDirectory() as tmpdir:
    output_path = Path(tmpdir) / "test_crate"
    
    # Create facade and add registered models
    facade = SchemaFacade()
    facade.add_all_registered_models()
    
    # Add model instances
    facade.add_model_instance(person, "alice_researcher")
    facade.add_model_instance(org, "research_institute")
    
    # Export using add_schema_to_crate
    from lib_ro_crate_schema.crate.jsonld_utils import add_schema_to_crate
    from rocrate.rocrate import ROCrate
    
    crate = ROCrate()
    crate.name = "Test RO-Crate"
    crate.description = "Testing published package"
    final_crate = add_schema_to_crate(facade, crate)
    final_crate.write(output_path)
    
    # Verify the crate was created
    metadata_file = output_path / "ro-crate-metadata.json"
    assert metadata_file.exists(), "ro-crate-metadata.json not created"
    
    # Load and verify content
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    # Verify basic structure
    assert "@context" in metadata, "Missing @context"
    assert "@graph" in metadata, "Missing @graph"
    
    # Count entities
    graph = metadata["@graph"]
    
    # Look for our entity types
    type_counts = {}
    for item in graph:
        entity_type = item.get("@type", "Unknown")
        if isinstance(entity_type, list):
            for t in entity_type:
                type_counts[t] = type_counts.get(t, 0) + 1
        else:
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
    
    # Verify we have our custom types
    has_person = "Person" in type_counts
    has_org = "Organization" in type_counts
    
    assert has_person or has_org, "No custom entity types found"
    
    print("SUCCESS: All checks passed!")
    print(f"- Created RO-Crate with {len(graph)} entities")
    print(f"- Entity types: {', '.join(f'{k}: {v}' for k, v in sorted(type_counts.items()))}")
    if has_person:
        print(f"- ✓ Person entities found")
    if has_org:
        print(f"- ✓ Organization entities found")
""")
        print("   ✓ Test script created")
        
        # Step 4: Run the test script
        print("\n4. Running test script...")
        result = subprocess.run(
            [str(python_path), str(test_script)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("\n--- Test Script Output ---")
        print(result.stdout)
        if result.stderr:
            print("--- Stderr ---")
            print(result.stderr)
        print("-------------------------\n")
        
        if result.returncode != 0:
            print("   ✗ Test script failed!")
            assert False, f"Test script execution failed with code {result.returncode}"
        
        # Verify success message
        assert "SUCCESS: All checks passed!" in result.stdout, "Test did not complete successfully"
        print("   ✓ Test script passed all checks")
        
        print(f"\n{'='*60}")
        print("✓ All Tests Passed!")
        print(f"{'='*60}")
        print("\nThe published package on TestPyPI works correctly:")
        print("- Installation successful")
        print("- Import successful")
        print("- Decorator pattern works")
        print("- RO-Crate creation works")
        print("- Export functionality works")
        print("- Metadata validation passed")


if __name__ == "__main__":
    test_install_from_testpypi()
