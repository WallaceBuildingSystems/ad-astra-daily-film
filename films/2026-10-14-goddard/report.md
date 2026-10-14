# 2026-10-14 Goddard: posted

The 9:48 am run stopped at the Runway credential check (401, see the first note below). James asked at 11:37 am to produce today's film now, for review, so it was made in his session on Runway's developer site in the browser pane.

- Title: The Times Regrets the Error. 17 phrases, 97 words, Wallace Jax Meridian take 4 at tempo 1.25, 42.2 seconds of voice, 44.5 seconds with the end card, minus 14.0 LUFS, peak minus 1.2.
- Pictures: 16 Nano Banana Pro stills (320 credits), redos of s06_lox (white margins) and s10_rise (twice: a finned modern rocket, then a flame pointing up; the third has the motor at the top and the exhaust blasting down), 8 Gen-4.5 clips at 5 seconds (480 credits). 860 credits, 90,609 left after.
- Kit changes: counters take prefix, unit, a_label and b_label; long labels and counter source lines break onto 2 lines at the last full stop.
- Sent for review at 12:45 pm, both cuts staged in Upload Post (uploads f9cb7283712247aa9a3c8331fd750de3 and 7755fbcc0b71470e848ad65e4f51e196). James chose "Post now".
- Posted 1:10 pm: X https://x.com/joinadastra/status/2110191373387260102 (request a4b1a81131b845da8c42de762a70c2be), Instagram https://www.instagram.com/reel/DedR2ybkatd/ (request 8c6e832b6a5c490f9277afe5e8bf3b53).
- At 1:10 pm James asked that no post name Runway or ElevenLabs. Both posts had gone out with the line; a cancel of the Instagram job came too late. James chose to leave the X post as is. captions.json now holds the clean captions and, under posted_14_october_with_tool_line, what went out.
- The routine moved to the review flow: daily at 6:47 am Melbourne, ready by 9:00 am, posted only on James's approval, by 12:00 pm. The other session's 7:45 am task "Ad Astra film for review, 9am" is turned off (James chose this routine).

First note, from the 9:48 am run: Step 0.3 failed: `python3 kit/runway_api.py balance` answered 401, no developer key reached it. Fix: James restores a valid Runway developer key in the Default environment's network secret and sets its network access to Full.
