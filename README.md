# ResolveCollaboration
## Streamlining and Extending DaVinci Resolve's Live Collaboration
I'm developing an app that makes the Resolve Live Collaboration features better, and makes them work over the internet in a secure manner.

# Features
Under development
- Give a status list of PostgreSQL database connections, even before launching Resolve (currently the alternative is waiting the ~3-4 mins for Resolve to start, only to realize you have to reboot Resolve to re-establish the connection)[/list]
- Give a status list of all Users, whether they're connected to the server, when they were last seen online, and which project they're in[/list]
- Give a status list of projects, when they were last updated, and (ideally) by whom[/list]
- Simplify connecting to a WireGuard Tunnel for over-the-internet work[/list]
- Status updates of connection speed/ping through the VPN and to the Project Server[/list]
- Provide user-friendly symlink generation so that media addresses can be linked across systems (Windows C:/... to Mac /Users/... or wherever your paths are). This is supposedly doable using Mapped Media in Resolve but this seems to be a bit shoddy. Hopefully there can be a multiplatform symlink solution?[/list]

Implemented
- Nothing yet, except an example implementation
- Discoveries about the backend / internals of Resolve and how it deals with collaboration (see Discoveries.md)

# Motivation
In Oct 2019, I was in San Francisco working on an edit for [Veritasium](https://www.youtube.com/watch?v=QRt7LjqJ45k) a YouTube channel. My client, Derek (in Los Angeles) has plenty of editing skills too (in many respects better than me) and we were in crunch mode for this deadline.

We were on Premiere Pro at the time and decided to give their [Team Projects](https://www.adobe.com/creativecloud/team-projects.html) feature a try. As a developer this made me very excited - it's like Git but for timelines and projects!

We split the video in two and I edited the latter half while Derek edited the former half. The Team Projects feature, after all, was pretty buggy and confusing from time to time, but we were able to merge our timelines eventually and deliver on schedule.

For media storage, we have a shared Dropbox folder where all the media is stored and synced across the internet.

It worked, but imho Premiere is 10 years behind every other editing software (especially FCPX and Resolve) and both Derek and I were sick of its shortcomings.

We decided to give Resolve a chance (largely for it's seemingly BETTER collaboration features) and everywhere we asked there seemed to be this permeating feeling that "you could totally do it over internet (LA<->SF)". We tried, tried, tried, and tried, asking developers directly one day in the Burbank BM office (they were dismissive of the idea), until eventually giving up because we couldn't get past the "Resolve Collaboration Failed: Make sure you're not on a VPN" message.
