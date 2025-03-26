import os
import subprocess
import tomlkit
import argparse
import datetime
from pathlib import Path

def bump_version(version: str, bump: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if bump == "patch":
        patch += 1
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "major":
        major += 1
        minor = patch = 0
    else:
        raise ValueError("Bump must be 'patch', 'minor', or 'major'")
    return f"{major}.{minor}.{patch}"

def update_pyproject_version(bump_type: str, dry_run=False):
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        data = tomlkit.parse(f.read())

    current_version = data["project"]["version"]
    new_version = bump_version(current_version, bump_type)

    if not dry_run:
        data["project"]["version"] = new_version
        with open("..\pyproject.toml", "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(data))

    return current_version, new_version

def run_command(cmd, dry_run=False):
    print(f"→ {cmd}")
    if not dry_run:
        subprocess.run(cmd, shell=True, check=True)

def check_git_clean():
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("❌ Git working directory is not clean. Commit or stash changes before releasing.")
        exit(1)

def generate_changelog(version, previous_version):
    timestamp = datetime.date.today().isoformat()
    changelog_path = Path("CHANGELOG.md")
    entry = f"## v{version} - {timestamp}\n\n- _Describe changes here_\n\n"

    if changelog_path.exists():
        content = changelog_path.read_text()
        changelog_path.write_text(entry + content)
    else:
        changelog_path.write_text("# Changelog\n\n" + entry)

    print("📝 CHANGELOG.md updated")

def main():
    parser = argparse.ArgumentParser(description="Automate release flow")
    parser.add_argument("bump", choices=["patch", "minor", "major"], help="Type of version bump")
    parser.add_argument("--dry-run", action="store_true", help="Simulate everything without making changes")
    args = parser.parse_args()

    # Prevent releasing from any branch other than main
    branch = subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True).decode().strip()
    if branch != "main" and not args.dry_run:
        print(f"❌ You are on '{branch}', not 'main'. Release only from main!")
        exit(1)

    if not args.dry_run:
        check_git_clean()

    prev_version, new_version = update_pyproject_version(args.bump, dry_run=args.dry_run)

    print(f"\n🔧 Version bump: {prev_version} → {new_version}\n")

    run_command("rm -rf dist build *.egg-info", dry_run=args.dry_run)
    run_command("python -m build", dry_run=args.dry_run)

    run_command("git add pyproject.toml", dry_run=args.dry_run)
    run_command(f"git commit -m 'Release v{new_version}'", dry_run=args.dry_run)
    run_command(f"git tag v{new_version}", dry_run=args.dry_run)
    run_command("git push origin main --tags", dry_run=args.dry_run)

    generate_changelog(new_version, prev_version)

    wheel_path = f"dist/maply-{new_version}-py3-none-any.whl"
    release_notes = input("📝 GitHub release notes (press Enter to skip): ").strip()

    cmd = f'gh release create v{new_version} {wheel_path} -t "v{new_version}"'
    if release_notes:
        cmd += f' -n "{release_notes}"'

    run_command(cmd, dry_run=args.dry_run)

    print(f"\n✅ Release v{new_version} complete! 🎉")

if __name__ == "__main__":
    main()
