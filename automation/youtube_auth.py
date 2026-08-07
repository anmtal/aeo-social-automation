# -*- coding: utf-8 -*-
"""One-time YouTube OAuth. Run this ONCE locally, consent in the browser, and it
prints the three secrets to paste into automation/.env. After that the publisher
runs unattended using the refresh token.

    python automation/youtube_auth.py

Needs automation/client_secret.json — the OAuth client JSON you download from
Google Cloud (APIs & Services -> Credentials -> OAuth client ID -> Desktop app).
Nothing here is committed: client_secret.json and .env are gitignored.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SECRET = os.path.join(HERE, "client_secret.json")
CHANNEL_ID = "UCktLX860_6jJsSCd0utNrNg"  # The AEO Loop channel
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]


def main():
    if not os.path.exists(SECRET):
        sys.exit("Missing automation/client_secret.json.\n"
                 "Google Cloud -> APIs & Services -> Credentials -> Create OAuth client ID "
                 "-> Application type: Desktop app -> Download JSON -> save it as "
                 "automation/client_secret.json, then re-run this.")
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit("pip install google-auth-oauthlib google-api-python-client")

    flow = InstalledAppFlow.from_client_secrets_file(SECRET, SCOPES)
    # access_type=offline + prompt=consent guarantees a refresh_token is returned.
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent",
                                  open_browser=True,
                                  authorization_prompt_message="Opening your browser to authorize The AEO Loop uploads...")
    conf = (json.load(open(SECRET)).get("installed") or json.load(open(SECRET)).get("web") or {})
    if not creds.refresh_token:
        sys.exit("No refresh_token returned. Revoke the app's access at "
                 "myaccount.google.com/permissions and run this again.")

    kv = {
        "YOUTUBE_CLIENT_ID": conf.get("client_id", ""),
        "YOUTUBE_CLIENT_SECRET": conf.get("client_secret", ""),
        "YOUTUBE_REFRESH_TOKEN": creds.refresh_token,
        "YOUTUBE_CHANNEL_ID": CHANNEL_ID,
    }
    envp = os.path.join(HERE, ".env")
    kept = []
    if os.path.exists(envp):
        for line in open(envp, encoding="utf-8"):
            key = line.split("=", 1)[0].strip()
            if key not in kv:            # keep unrelated lines, replace the YOUTUBE_* ones
                kept.append(line.rstrip("\n"))
    out = kept + [f"{k}={v}" for k, v in kv.items()]
    has_music = any(l.startswith("YOUTUBE_MUSIC=") for l in kept)
    if not has_music:
        out.append("# YOUTUBE_MUSIC=C:\\Users\\anmta\\Downloads\\aeo-reels\\bed.mp3  (a YouTube-cleared mp3)")
    open(envp, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\nDONE. Wrote YOUTUBE_* credentials to automation/.env (refresh token hidden, not printed).")
    print("Next:  python automation/youtube_publisher.py --check")


if __name__ == "__main__":
    main()
