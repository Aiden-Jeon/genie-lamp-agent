#!/usr/bin/env python3
"""
Databricks App Deployment Script for Genie Lamp Agent

Handles both initial deployment and update deployment of Databricks apps.
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
        print(f"   {result.stdout}")

    return True


def deploy_app(app_name, target_env, profile, source_code_path, is_initial_deployment, working_dir=None):
    """
    Deploy a Databricks app.

    Args:
        app_name: Name of the app (e.g., 'genie-lamp-agent')
        target_env: Target environment (e.g., 'dev', 'prod')
        profile: Databricks profile name (e.g., 'DEFAULT')
        source_code_path: Path to source code in Workspace
        is_initial_deployment: True for first deployment, False for updates
        working_dir: Working directory for bundle commands (e.g., 'app')
    """

    print(f"\n{'='*60}")
    print(f"🚀 Genie Lamp Agent - Databricks App Deployment")
    print(f"{'='*60}")
    print(f"   App Name: {app_name}")
    print(f"   Environment: {target_env}")
    print(f"   Profile: {profile}")
    print(f"   Deployment Type: {'Initial' if is_initial_deployment else 'Update'}")
    if working_dir:
        print(f"   Working Directory: {working_dir}")
    print(f"{'='*60}\n")

    # Validate working directory if provided
    if working_dir:
        if not os.path.isdir(working_dir):
            print(f"❌ Error: Working directory '{working_dir}' does not exist")
            return False

        databricks_yml = os.path.join(working_dir, "databricks.yml")
        if not os.path.isfile(databricks_yml):
            print(f"❌ Error: databricks.yml not found in '{working_dir}'")
            return False

    # Step 1: Bundle deploy (both initial and update)
    bundle_cmd = f"databricks bundle deploy -t {target_env} -p {profile}"
    if not run_command(bundle_cmd, "Bundle deploy", cwd=working_dir):
        return False

    # Step 2: App start (only for initial deployment)
    if is_initial_deployment:
        start_cmd = f"databricks apps start {app_name} -p {profile}"
        if not run_command(start_cmd, "App start"):
            return False

    # Step 3: App deploy (both initial and update)
    deploy_cmd = f"databricks apps deploy {app_name} --source-code-path {source_code_path} -p {profile}"
    if not run_command(deploy_cmd, "App deploy"):
        return False

    print(f"\n{'='*60}")
    print(f"✅ Deployment completed successfully!")
    print(f"{'='*60}\n")
    print(f"📱 Access your app:")
    print(f"   Workspace > Apps > {app_name}")
    print(f"\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Genie Lamp Agent Databricks app with support for initial and update deployments"
    )

    parser.add_argument(
        "app_name", help="Name of the app (e.g., 'genie-lamp-agent')"
    )

    parser.add_argument(
        "--target", "-t", default="dev", help="Target environment (default: dev)"
    )

    parser.add_argument(
        "--profile",
        "-p",
        default="DEFAULT",
        help="Databricks profile name (default: DEFAULT)",
    )

    parser.add_argument(
        "--source-code-path",
        required=True,
        help="Path to source code in Workspace (e.g., /Workspace/Users/user@domain.com/.bundle/genie-lamp-agent/dev/files)",
    )

    parser.add_argument(
        "--working-dir",
        "-w",
        default=None,
        help="Working directory for bundle commands (e.g., 'app' for Genie Lamp Agent)",
    )

    parser.add_argument(
        "--initial",
        action="store_true",
        help="Flag for initial deployment (includes app start command)",
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Flag for update deployment (skips app start command)",
    )

    args = parser.parse_args()

    # Determine deployment type
    if args.initial and args.update:
        print("❌ Error: Cannot specify both --initial and --update")
        sys.exit(1)

    # Default to update if neither is specified
    is_initial = args.initial

    # Deploy the app
    success = deploy_app(
        app_name=args.app_name,
        target_env=args.target,
        profile=args.profile,
        source_code_path=args.source_code_path,
        is_initial_deployment=is_initial,
        working_dir=args.working_dir,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
