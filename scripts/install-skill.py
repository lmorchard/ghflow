#!/usr/bin/env python3
"""Link the ghflow source skill into explicitly selected agent directories."""
import argparse
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent
PERSONAL = {"claude": ".claude/skills", "codex": ".agents/skills", "opencode": ".config/opencode/skills"}
PROJECT = {"claude": ".claude/skills", "codex": ".agents/skills", "opencode": ".opencode/skills"}


def install(destinations, source=SOURCE):
    pairs = []
    for item in destinations:
        if isinstance(item, tuple):
            dest, src = item
            src = src.resolve()
        else:
            dest = item
            src = source.resolve()
        if not (src / "SKILL.md").is_file():
            raise ValueError(f"Missing source skill: {src}")
        pairs.append((dest, src))

    # Check the full request before creating any links.
    for destination, src in pairs:
        for ancestor in destination.parents:
            if os.path.lexists(ancestor) and not ancestor.is_dir():
                raise ValueError(f"Destination ancestor is not a directory: {ancestor}")
        if os.path.lexists(destination):
            if destination.is_symlink() and destination.resolve() == src:
                continue
            raise ValueError(f"Refusing to overwrite existing entry: {destination}")
    for destination, src in pairs:
        if destination.is_symlink() and destination.resolve() == src:
            print(f"Already linked: {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        # symlink_to refuses a destination created after the preflight too.
        destination.symlink_to(src, target_is_directory=True)
        print(f"Linked: {destination} -> {src}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agents", nargs="+", choices=PERSONAL, help="Agent destinations to install")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--home", type=Path, default=None, help="Personal home (default: current user's home)")
    scope.add_argument("--project", type=Path, help="Install into this target project")
    args = parser.parse_args()
    root = (args.project or args.home or Path.home()).expanduser().resolve()
    locations = PROJECT if args.project else PERSONAL
    role_skills = {
        "ghflow": SOURCE,
        "ghflow-build": SOURCE / "skills/build",
        "ghflow-build-slim": SOURCE / "skills/build-slim",
        "ghflow-review": SOURCE / "skills/review",
        "ghflow-review-slim": SOURCE / "skills/review-slim",
        "ghflow-define": SOURCE / "skills/define",
        "ghflow-coord": SOURCE / "skills/coord",
    }
    available_skills = {k: v for k, v in role_skills.items() if (v / "SKILL.md").is_file()}
    destinations = []
    for name in dict.fromkeys(args.agents):
        for skill_name, skill_src in available_skills.items():
            destinations.append((root / locations[name] / skill_name, skill_src))
    try:
        install(destinations)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
