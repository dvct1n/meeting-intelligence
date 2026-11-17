> **Synthetic example.** This report was generated from a made-up transcript to show the output format; it is not a measurement of model quality.

# Mobile app launch planning

*2025-07-01 09:00 UTC · duration 01:38 · 3 speaker(s)*

## Summary

The team reviewed release readiness: QA is nearly done with two minor bugs and the new search endpoint is on staging. They agreed to launch on Friday the 14th, with the app submitted for store review on Monday to leave a buffer against slow reviews.

**Topics:** launch date · QA status · app-store review · migration notes

## Decisions

- Launch the mobile app on Friday the 14th — _The remaining QA bugs are minor and do not block the release_
- Submit the app for store review on Monday — _Leaves a buffer if the review takes longer than two days_

## Action items

| Task | Owner | Deadline |
|---|---|---|
| Update the changelog and the store listing | Linh | by Thursday |
| Finish the backend migration notes | Speaker 3 | tomorrow |
| Monitor the app-store review status | Minh | — |

## Speakers

- **Speaker 1** — Chaired the meeting, proposed the Friday launch and the Monday submission.
- **Speaker 2** — Reported QA status and took the changelog and store listing.
- **Speaker 3** — Reported backend progress, owns the migration notes and raised the review-delay risk.

## Topic timeline

- `00:00–00:38` Status check: QA has two non-blocking bugs left and the search endpoint is on staging.
- `00:39–01:38` The team settles on a Friday launch, assigns the changelog and migration notes, and plans a Monday app-store submission as a buffer.

## Transcript

`00:00` **Speaker 1**: Thanks everyone for joining. The goal today is to agree on the launch date for the mobile app and who owns what.  
`00:10` **Speaker 2**: QA finished the regression run yesterday. We have two minor bugs left, neither blocks the release.  
`00:25` **Speaker 3**: On the backend side the new search endpoint is deployed to staging. I still need to write the migration notes.  
`00:39` **Speaker 1**: Then let's ship on Friday the 14th. Linh, can you update the changelog and the store listing by Thursday?  
`00:56` **Speaker 2**: Yes, I'll take the changelog and the store listing, done by Thursday evening.  
`01:05` **Speaker 3**: I'll finish the migration notes tomorrow. One risk: if the app-store review takes longer than two days we slip.  
`01:23` **Speaker 1**: Agreed. Let's submit for review on Monday so we have a buffer, and Minh will monitor the review status.  
