# 2026-10-16 film: FAILED, no film made

Routine run at 6:48 am Melbourne (+1100). Step 0.3: `python3 kit/runway_api.py balance` returned 401, no developer key reached Runway. The network secret for api.dev.runwayml.com is missing from this environment, the same failure as 14 and 15 October. Nothing made, staged, posted or scheduled. Next in queue: Willis Carrier.

Fix: re-attach the Runway secret to the environment this routine runs in, or make the film in James's session through the browser fallback in PLAYBOOK.md.

Second run, 1:26 pm Melbourne (+1100): balance check still 401 (direct call to api.dev.runwayml.com also 401). Still nothing made, staged, posted or scheduled; the 9:00 am review deadline has passed.
