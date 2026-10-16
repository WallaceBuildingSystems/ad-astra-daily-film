# 2026-10-16 film: FAILED, no film made

Routine run at 6:48 am Melbourne (+1100). Step 0.3: `python3 kit/runway_api.py balance` returned 401, no developer key reached Runway. The network secret for api.dev.runwayml.com is missing from this environment, the same failure as 14 and 15 October. Nothing made, staged, posted or scheduled. Next in queue: Willis Carrier.

Fix: re-attach the Runway secret to the environment this routine runs in, or make the film in James's session through the browser fallback in PLAYBOOK.md.

Second run, 1:26 pm Melbourne (+1100): balance check still 401 (direct call to api.dev.runwayml.com also 401). Still nothing made, staged, posted or scheduled; the 9:00 am review deadline has passed.

Third run, 1:30 pm Melbourne (+1100): Runway now answers (creditBalance 89,164), so the 401 is fixed. New blocker at step 1: no primary source can be opened. WebFetch fails with getaddrinfo ENOTFOUND for every host tried (asme.org, patents.google.com, eia.gov, si.edu, wikipedia.org), and curl through the agent proxy gets CONNECT 403 for eia.gov. Only WebSearch snippets are available, which are not sources opened in this run (ROUTINE.md hard rule). Nothing made, staged, posted or scheduled; no Runway credits spent. Next in queue: Willis Carrier.

Fix: allow outbound HTTPS to the source sites (or the full-access network policy) for this environment, then rerun.
