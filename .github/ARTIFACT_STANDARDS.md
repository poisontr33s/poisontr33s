# GitHub Actions Artifact Management Standards

## Overview

This document establishes standardized practices for artifact management across all GitHub Actions workflows in this repository. These standards ensure consistency, avoid naming conflicts, and provide clear guidelines for future contributors.

## Artifact Action Versions

### Required Versions
- **Upload artifacts**: `actions/upload-artifact@v4` exclusively
- **Download artifacts**: `actions/download-artifact@v4` exclusively

### Deprecated Versions
❌ **DO NOT USE**: `actions/upload-artifact@v2`, `actions/upload-artifact@v3`
❌ **DO NOT USE**: `actions/download-artifact@v2`, `actions/download-artifact@v3`

## Artifact Naming Conventions

### Standard Jobs
For single-instance jobs, use descriptive names:
```yaml
- name: Upload logs
  uses: actions/upload-artifact@v4
  with:
    name: job-name-logs
    path: logs/
```

### Matrix Jobs
For matrix jobs, **ALWAYS** include matrix variables in artifact names to ensure uniqueness:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    node-version: [16, 18, 20]

steps:
  - name: Upload build artifacts
    uses: actions/upload-artifact@v4
    with:
      name: build-${{ matrix.os }}-node${{ matrix.node-version }}
      path: dist/
      
  - name: Upload test results
    uses: actions/upload-artifact@v4
    with:
      name: test-results-${{ matrix.os }}-node${{ matrix.node-version }}
      path: test-results/
```

### Multi-Matrix Variables
When using multiple matrix dimensions, include all relevant variables:
```yaml
name: coverage-${{ matrix.os }}-${{ matrix.python-version }}-${{ matrix.test-suite }}
```

## Artifact Lifecycle Management

### Retention Periods
- **Development/CI artifacts**: 7-30 days
- **Release artifacts**: 90 days or longer
- **Debug/log artifacts**: 7-14 days

### Path Specifications
- Use specific paths, avoid wildcards when possible
- Include relevant subdirectories
- Document expected artifact contents

## Download Patterns

### Single Artifact Download
```yaml
- name: Download build artifacts
  uses: actions/download-artifact@v4
  with:
    name: build-artifacts
    path: ./downloaded-artifacts
```

### Multiple Artifact Download
```yaml
- name: Download all artifacts
  uses: actions/download-artifact@v4
  with:
    path: ./all-artifacts
```

### Matrix-Specific Downloads
```yaml
- name: Download matrix-specific artifact
  uses: actions/download-artifact@v4
  with:
    name: build-${{ matrix.os }}-node${{ matrix.node-version }}
    path: ./matrix-artifacts
```

## Migration Guidelines

### From v2/v3 to v4
1. Update action version: `@v3` → `@v4`
2. Review artifact naming for matrix compatibility
3. Verify path specifications
4. Test workflow execution

### Breaking Changes in v4
- Artifact upload/download behavior may differ slightly
- Ensure compatibility testing before deploying

## Examples

### Current Repository Usage
See `.github/workflows/add-contributors.yml` for reference implementation using v4 standards.

### Future Matrix Implementation
When implementing matrix jobs, follow the naming pattern:
```yaml
name: artifact-name-${{ matrix.variable1 }}-${{ matrix.variable2 }}
```

## Enforcement

- All new workflows MUST follow these standards
- Existing workflows should be updated to v4 during maintenance
- Pull requests introducing deprecated versions will be rejected
- Code reviews should verify artifact naming compliance

## Resources

- [GitHub Actions Artifact Documentation](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)
- [actions/upload-artifact@v4](https://github.com/actions/upload-artifact)
- [actions/download-artifact@v4](https://github.com/actions/download-artifact)

---

**Last Updated**: 2023-10-05
**Standard Version**: 1.0
**Applies to**: All workflows in `poisontr33s/poisontr33s` repository