#!/usr/bin/env python3
"""
Production Deployment Script for Genie Lamp Agent

Automates the complete production deployment workflow:
1. Build frontend
2. Deploy bundle (which handles app deployment automatically)

Configuration:
- Environment: prod
- Profile: krafton-sandbox
- App Name: genie-lamp-agent

Note: Databricks Asset Bundle (databricks.yml) handles the complete app lifecycle.
      No separate app deploy commands needed - bundle deploy does everything.
"""

import subprocess
import sys
import argparse
import os
from pathlib import Path


def run_command(command, description, cwd=None):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"   Command: {command}")
    if cwd:
        print(f"   Working directory: {cwd}")

    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)

    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"   stderr: {result.stderr}")
        if result.stdout:
            print(f"   stdout: {result.stdout}")
        return False

    print(f"✅ {description} completed")
    if result.stdout:
        # For long outputs, show a preview
        lines = result.stdout.strip().split('\n')
        if len(lines) > 10:
            print(f"   Output (first 5 lines):")
            for line in lines[:5]:
                print(f"   {line}")
            print(f"   ... ({len(lines) - 10} more lines)")
            print(f"   Output (last 5 lines):")
            for line in lines[-5:]:
                print(f"   {line}")
        else:
            for line in lines:
                print(f"   {line}")

    return True


def deploy_prod():
    """
    Deploy Genie Lamp Agent to production environment.

    Uses Databricks Asset Bundle deployment which handles the complete lifecycle.
    """

    # Hardcoded production configuration
    APP_NAME = "genie-lamp-agent"
    TARGET_ENV = "prod"
    PROFILE = "krafton-sandbox"

    print(f"\n{'='*70}")
    print(f"🚀 Genie Lamp Agent - Production Deployment")
    print(f"{'='*70}")
    print(f"   App Name: {APP_NAME}")
    print(f"   Environment: {TARGET_ENV}")
    print(f"   Profile: {PROFILE}")
    print(f"{'='*70}\n")

    # Validate we're in project root
    if not os.path.isfile("databricks.yml"):
        print(f"❌ Error: databricks.yml not found in current directory")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Make sure you're running this from the project root")
        return False

    # Validate frontend directory exists
    if not os.path.isdir("frontend"):
        print(f"❌ Error: frontend directory not found")
        print(f"   Make sure you're running this from the project root")
        return False

    # Step 1: Build frontend
    print(f"\n{'='*70}")
    print(f"📦 Step 1: Building Frontend")
    print(f"{'='*70}")

    # Temporarily move .env.local to use .env.production settings
    env_local_path = Path("frontend/.env.local")
    env_local_backup = Path("frontend/.env.local.backup")
    env_local_existed = False

    if env_local_path.exists():
        print(f"   ⚠️  Found .env.local (localhost config), temporarily moving it aside")
        env_local_path.rename(env_local_backup)
        env_local_existed = True

    try:
        frontend_build_cmd = "npm run build"
        if not run_command(frontend_build_cmd, "Frontend build", cwd="frontend"):
            print(f"\n❌ Frontend build failed. Deployment aborted.")
            return False
    finally:
        # Restore .env.local if it existed
        if env_local_existed and env_local_backup.exists():
            env_local_backup.rename(env_local_path)
            print(f"   ✅ Restored .env.local")

    print(f"\n✅ Frontend build completed successfully")

    # Step 2: Bundle deploy (syncs files to workspace)
    print(f"\n{'='*70}")
    print(f"📦 Step 2: Deploying Bundle")
    print(f"{'='*70}")
    print(f"   Syncing files to workspace\n")

    bundle_cmd = f"databricks bundle deploy -t {TARGET_ENV} -p {PROFILE}"
    if not run_command(bundle_cmd, "Bundle deploy"):
        print(f"\n❌ Bundle deploy failed. Deployment aborted.")
        return False

    # Step 3: Deploy/update the app
    print(f"\n{'='*70}")
    print(f"📦 Step 3: Deploying App")
    print(f"{'='*70}")
    print(f"   Deploying {APP_NAME}\n")

    # For prod, use shared workspace path
    source_code_path = "/Workspace/Shared/databricks-agent-poc/genie-lamp-app/files"
    print(f"   Source code path: {source_code_path}")

    # Check if app exists
    check_cmd = f"databricks apps get {APP_NAME} -p {PROFILE}"
    check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

    if check_result.returncode == 0:
        # App exists - update it
        print(f"   ℹ️  App exists, deploying update...")
        app_cmd = f"databricks apps deploy {APP_NAME} --source-code-path '{source_code_path}' -p {PROFILE}"
    else:
        # App doesn't exist - create it
        print(f"   ℹ️  App doesn't exist, creating with bundle...")
        print(f"   Note: New apps should be created by bundle deploy")
        # For new apps, we still need to deploy after bundle creates it
        app_cmd = f"databricks apps deploy {APP_NAME} --source-code-path '{source_code_path}' -p {PROFILE}"

    if not run_command(app_cmd, "App deployment"):
        print(f"\n⚠️  App deployment command failed")
        print(f"   The app may have been deployed by bundle")
        print(f"   Check: databricks apps get {APP_NAME} -p {PROFILE}")
        # Don't fail here - bundle might have handled it
    else:
        print(f"\n✅ App deployed/updated successfully")

    # Success summary
    print(f"\n{'='*70}")
    print(f"✅ Production Deployment Completed Successfully!")
    print(f"{'='*70}\n")
    print(f"📱 Access your production app:")
    print(f"   Workspace > Apps > {APP_NAME}")
    print(f"\n🔍 Verify deployment:")
    print(f"   databricks apps list -p {PROFILE} | grep {APP_NAME}")
    print(f"   databricks apps get {APP_NAME} -p {PROFILE}")
    print(f"\n📋 View logs (if needed):")
    print(f"   databricks apps logs {APP_NAME} -p {PROFILE}")
    print(f"\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Genie Lamp Agent to production environment with automated frontend build",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to production (handles both initial and updates)
  python deploy_prod.py

Production Configuration:
  Environment: prod
  Profile: krafton-sandbox
  App Name: genie-lamp-agent

Note: This script must be run from the project root directory.
      Bundle deploy automatically handles app lifecycle (create/update).
        """
    )

    args = parser.parse_args()

    # Deploy to production
    success = deploy_prod()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
