# Ad Astra daily film

The daily film for Ad Astra (joinadastra.com): 1 builder a day, about 40 seconds, an ElevenLabs voice over Runway pictures, cut for X and Instagram Reels, ready for James's review by 9:00 am Melbourne and posted through Upload Post with hashtags once he approves, by 12:00 pm.

- A Claude Code routine runs ROUTINE.md every morning, in the Default cloud environment, which holds the Runway API credential and has full network access.
- PLAYBOOK.md: the builder queue and the rules. Edit the queue to steer the films.
- LOG.md: 1 line a film, with the Upload Post request ids.
- films/: each film's research, script, shot list, edit list, captions and report. Pictures, video and sound stay out of the repository.
- kit/: the tools that make the film.

To stop: pause or delete the routine at claude.ai/code/routines. To stop one film: cancel its posts in Upload Post.
