#!/bin/bash

# Repository Structure Setup Script
# Creates standardized folder structure for GitHub repositories

set -e

echo "🎯 Repository Structure Setup"
echo "=============================="

# Define folder structure
FOLDERS=(
    "docs"
    "assets" 
    "scripts"
    "src"
    "tests"
)

# Create folder structure
echo "📁 Creating folder structure..."
for folder in "${FOLDERS[@]}"; do
    if [ ! -d "$folder" ]; then
        mkdir -p "$folder"
        echo "  ✓ Created: $folder/"
    else
        echo "  ⏭ Exists: $folder/"
    fi
done

# Create .gitkeep files with descriptions
echo "📄 Setting up folder documentation..."

# Assets folder
if [ ! -f "assets/.gitkeep" ]; then
    cat > "assets/.gitkeep" << 'EOF'
# Assets Directory

This directory contains images, resources, and other assets referenced in documentation and guides.

## Structure
- Place images referenced in migration guides here
- Organize by project or guide type when needed
- Use descriptive filenames for better organization
EOF
    echo "  ✓ Created: assets/.gitkeep"
fi

# Scripts folder  
if [ ! -f "scripts/.gitkeep" ]; then
    cat > "scripts/.gitkeep" << 'EOF'
# Scripts Directory

This directory contains automation scripts and utilities.

## Structure
- setup-repo-structure.sh: Repository initialization script
- Migration and setup utilities
- CI/CD helper scripts
EOF
    echo "  ✓ Created: scripts/.gitkeep"
fi

# Source folder
if [ ! -f "src/.gitkeep" ]; then
    cat > "src/.gitkeep" << 'EOF'
# Source Code Directory

This directory contains source code and relevant implementation files.

## Structure
- Organize by language or project
- Include main application code
- Follow language-specific conventions
EOF
    echo "  ✓ Created: src/.gitkeep"
fi

# Tests folder
if [ ! -f "tests/.gitkeep" ]; then
    cat > "tests/.gitkeep" << 'EOF'
# Tests Directory

This directory contains test files for validating automation pipelines and functionality.

## Structure
- Unit tests for scripts and automation
- Integration tests for workflows  
- Validation tests for folder structure creation
EOF
    echo "  ✓ Created: tests/.gitkeep"
fi

# Docs folder
if [ ! -f "docs/.gitkeep" ]; then
    cat > "docs/.gitkeep" << 'EOF'
# Documentation Directory

This directory contains documentation, guides, and related materials.

## Structure
- migration_guide.md: Primary migration documentation
- Additional guides and documentation
- Technical specifications and requirements
EOF
    echo "  ✓ Created: docs/.gitkeep"
fi

# Create template migration guide if it doesn't exist
if [ ! -f "docs/migration_guide.md" ]; then
    echo "📋 Creating template migration guide..."
    cat > "docs/migration_guide.md" << 'EOF'
# Migration Guide Template

## Executive Summary
This document provides a comprehensive, systematic approach for project or system migration, employing best practices to ensure data integrity, minimal downtime, and optimal post-migration performance.

## Table of Contents
1. [Pre-Migration Analysis](#1-pre-migration-analysis)
2. [Preparation Phase](#2-preparation-phase)
3. [Migration Strategy](#3-migration-strategy)
4. [Implementation](#4-implementation)
5. [Post-Migration Setup](#5-post-migration-setup)
6. [Verification & Optimization](#6-verification--optimization)

---

## 1. Pre-Migration Analysis

### 1.1 Current State Assessment
- **Objective**: Document existing system/process state
- **Tasks**:
  - [ ] Inventory current components and dependencies
  - [ ] Document current workflows and processes
  - [ ] Identify potential migration challenges
  - [ ] Assess resource requirements

### 1.2 Target State Definition
- **Objective**: Define desired end state after migration
- **Tasks**:
  - [ ] Specify target architecture/system
  - [ ] Document required features and capabilities
  - [ ] Define success criteria and metrics
  - [ ] Establish testing requirements

---

## 2. Preparation Phase

### 2.1 Environment Setup
- **Objective**: Prepare migration infrastructure
- **Tasks**:
  - [ ] Set up development/staging environments
  - [ ] Install required tools and dependencies
  - [ ] Configure access permissions and credentials
  - [ ] Establish communication channels

### 2.2 Backup Strategy
- **Objective**: Ensure data protection during migration
- **Tasks**:
  - [ ] Create comprehensive backup plan
  - [ ] Implement backup verification procedures
  - [ ] Document restoration procedures
  - [ ] Test backup and restore processes

---

## 3. Migration Strategy

### 3.1 Migration Approach
- **Objective**: Define migration methodology
- **Tasks**:
  - [ ] Choose migration strategy (big bang, phased, parallel)
  - [ ] Define migration phases and milestones
  - [ ] Create rollback procedures
  - [ ] Establish timeline and resource allocation

### 3.2 Risk Assessment
- **Objective**: Identify and mitigate migration risks
- **Tasks**:
  - [ ] Document potential risks and impacts
  - [ ] Develop mitigation strategies
  - [ ] Create contingency plans
  - [ ] Define escalation procedures

---

## 4. Implementation

### 4.1 Migration Execution
- **Objective**: Execute planned migration steps
- **Tasks**:
  - [ ] Execute migration scripts/procedures
  - [ ] Monitor migration progress
  - [ ] Document any deviations or issues
  - [ ] Implement corrective actions as needed

### 4.2 Real-time Monitoring
- **Objective**: Ensure migration proceeds as planned
- **Tasks**:
  - [ ] Monitor system performance and stability
  - [ ] Track migration progress against timeline
  - [ ] Log all activities and decisions
  - [ ] Communicate status to stakeholders

---

## 5. Post-Migration Setup

### 5.1 System Configuration
- **Objective**: Configure target system for optimal operation
- **Tasks**:
  - [ ] Apply configuration settings
  - [ ] Set up monitoring and alerting
  - [ ] Configure security settings
  - [ ] Implement backup procedures

### 5.2 User Training and Documentation
- **Objective**: Ensure smooth transition for end users
- **Tasks**:
  - [ ] Create user documentation and guides
  - [ ] Conduct training sessions
  - [ ] Set up support channels
  - [ ] Gather user feedback

---

## 6. Verification & Optimization

### 6.1 Testing and Validation
- **Objective**: Verify migration success and system functionality
- **Tasks**:
  - [ ] Execute comprehensive testing plan
  - [ ] Validate data integrity and completeness
  - [ ] Performance testing and optimization
  - [ ] Security testing and validation

### 6.2 Documentation and Knowledge Transfer
- **Objective**: Document migration outcomes and lessons learned
- **Tasks**:
  - [ ] Document final system configuration
  - [ ] Create troubleshooting guides
  - [ ] Record lessons learned and best practices
  - [ ] Archive migration artifacts and documentation

---

## Migration Metrics & KPIs

### Success Criteria
- **Data Integrity**: 100% critical data successfully migrated
- **Downtime**: Minimize service interruption
- **Functionality**: All critical features operational post-migration
- **Performance**: System performance meets or exceeds baseline
- **Security**: No security vulnerabilities introduced

### Risk Mitigation
- **Data Loss**: Comprehensive backup and verification strategies
- **Service Interruption**: Phased migration with fallback options
- **Compatibility Issues**: Thorough pre-migration analysis and testing
- **Performance Issues**: Load testing and performance optimization

---

## Conclusion

This migration guide provides a structured approach to ensure successful project transitions. Regular review and adaptation of these procedures based on specific project requirements and lessons learned will improve future migration outcomes.

For specific migration scenarios, customize the relevant sections and add domain-specific requirements, tools, and procedures.
EOF
    echo "  ✓ Created: docs/migration_guide.md"
fi

echo ""
echo "✅ Repository structure setup complete!"
echo ""
echo "📊 Structure Summary:"
for folder in "${FOLDERS[@]}"; do
    echo "  📁 $folder/"
done

echo ""
echo "📚 Next Steps:"
echo "  1. Review and customize docs/migration_guide.md for your project"
echo "  2. Add project-specific assets to assets/"
echo "  3. Implement source code in src/"
echo "  4. Create tests in tests/"
echo "  5. Add additional automation scripts to scripts/"