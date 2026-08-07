@echo off
REM Fired daily by Windows Task Scheduler (~15 min before the afternoon YouTube slot).
REM Renders the next reel, drops a silent copy for manual Instagram, auto-posts to YouTube.
cd /d "C:\Users\anmta\.claude\AEO Social Automation"
"C:\Users\anmta\AppData\Local\Programs\Python\Python313\python.exe" automation\daily_reel.py >> content\daily-reel.log 2>&1
