"""
Daily Scout — Social Posting Script (Delayed)
Runs ~3h after the newsletter pipeline to publish social content.

Usage:
  python social_post.py                    # Posts the latest edition
  python social_post.py --edition 005      # Posts a specific edition
  python social_post.py --dry-run          # Validates without posting
  python social_post.py --preview          # Shows the content that would be posted

Environment:
  LINKEDIN_ACCESS_TOKEN  — OAuth token (GitHub Secret)
  LINKEDIN_PERSON_URN    — Optional: your person URN (auto-resolved if not set)
  DRY_RUN                — "true" to skip actual posting
  EDITION_NUMBER         — Edition to post (fallback to latest artifact)
"""

import argparse
import glob
import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("daily-scout.social-post")


def find_latest_artifact(output_dir: str = "output/social") -> str | None:
    """Find the most recent social artifact file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(base_dir, output_dir, "social_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    return files[-1]


def run_social_posting(edition: str | None = None, dry_run: bool = False,
                       preview_only: bool = False) -> bool:
    """
    Load social artifact and post to all configured platforms.

    Args:
        edition: Specific edition number, or None for latest
        dry_run: Validate but don't actually post
        preview_only: Just print the content, don't post

    Returns:
        True if all posts succeeded (or dry_run)
    """
    from social.content_adapter import load_social_artifact, update_social_artifact
    from social.linkedin import post_text

    # ── Find artifact ──
    if edition:
        artifact = load_social_artifact(edition)
        if not artifact:
            logger.error(f"No social artifact found for edition {edition}")
            return False
    else:
        # Try env var first, then latest file
        env_edition = os.environ.get("EDITION_NUMBER")
        if env_edition:
            artifact = load_social_artifact(env_edition)
            edition = env_edition
        if not artifact:
            latest_path = find_latest_artifact()
            if not latest_path:
                logger.error("No social artifacts found in output/social/")
                return False
            with open(latest_path, "r", encoding="utf-8") as f:
                artifact = json.load(f)
            edition = artifact.get("edition", "???")
            logger.info(f"Using latest artifact: {latest_path}")

    logger.info(f"Social posting for edition #{edition}")
    logger.info(f"Generated at: {artifact.get('generated_at', 'unknown')}")

    platforms = artifact.get("platforms", {})
    if not platforms:
        logger.warning("No platform content in artifact")
        return False

    all_success = True

    # ── LinkedIn ──
    if "linkedin" in platforms:
        li = platforms["linkedin"]

        if li.get("status") == "posted":
            logger.info("LinkedIn: already posted — skipping")
        else:
            content = li.get("content", {})
            post_body = content.get("linkedin_post", "")

            if not post_body:
                logger.error("LinkedIn: no post content found in artifact")
                all_success = False
            else:
                # ── Preview mode ──
                if preview_only:
                    print("\n" + "=" * 60)
                    print("LINKEDIN POST PREVIEW")
                    print("=" * 60)
                    print(f"Edition: #{edition}")
                    print(f"Chars: {len(post_body)}")
                    print(f"Hook: {content.get('hook_line', 'N/A')}")
                    print(f"Hashtags: {content.get('hashtags', [])}")
                    print("-" * 60)
                    # Render \n as actual newlines for readability
                    print(post_body.replace("\\n", "\n"))
                    print("=" * 60 + "\n")
                    return True

                # ── Post ──
                logger.info(f"LinkedIn: posting {len(post_body)} chars...")
                result = post_text(post_body, dry_run=dry_run)

                if result["success"]:
                    status = "dry_run" if dry_run else "posted"
                    update_social_artifact(
                        edition, "linkedin",
                        status=status,
                        post_id=result.get("post_id"),
                    )
                    logger.info(f"LinkedIn: {status}")
                else:
                    update_social_artifact(
                        edition, "linkedin",
                        status="failed",
                        error=result.get("error"),
                    )
                    logger.error(f"LinkedIn: failed — {result.get('error')}")
                    all_success = False

    # Future: Instagram, Twitter/X etc.

    return all_success


def main():
    parser = argparse.ArgumentParser(description="Daily Scout — Social Posting")
    parser.add_argument("--edition", type=str, help="Edition number to post")
    parser.add_argument("--dry-run", action="store_true", help="Validate without posting")
    parser.add_argument("--preview", action="store_true", help="Show content preview only")
    args = parser.parse_args()

    # Also respect env var
    dry_run = args.dry_run or os.environ.get("DRY_RUN", "false").lower() == "true"

    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║  DAILY SCOUT — SOCIAL POSTING (Delayed)         ║")
    logger.info("║  Correspondente: AYA                              ║")
    logger.info("╚══════════════════════════════════════════════════╝")

    if args.preview:
        logger.info("MODE: preview only")
    elif dry_run:
        logger.info("MODE: dry-run (no actual posting)")
    else:
        logger.info("MODE: live posting")

    success = run_social_posting(
        edition=args.edition,
        dry_run=dry_run,
        preview_only=args.preview,
    )

    if success:
        logger.info("Social posting complete!")
    else:
        logger.error("Social posting had failures")
        sys.exit(1)


if __name__ == "__main__":
    main()
