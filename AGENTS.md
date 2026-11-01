# Project working rules

## Docker delivery and user validation

User instruction dated 2026-10-29: after an item is complete and the user has
personally checked and confirmed it is correct, incorporate it into Docker immediately.

- Implement and test changes as a `candidate` image first so the user has something concrete to review.
- Automated tests and assistant review do not constitute user acceptance.
- After explicit user acceptance of the stated item/version, update Docker delivery,
  rerun relevant container tests, record image ID, source hashes, checks and the user
  acceptance reference in `docker/RELEASES.md`, then tag the accepted version.
- Keep the last accepted image/tag until its replacement is accepted. Do not tag a
  candidate as `accepted`, `stable`, or `latest` merely because automated tests passed.
- Preserve the DT core and parameterized profiles. CAD V5 and the evaluated MuJoCo
  baseline are currently different geometries; never silently claim they are synchronized.
- Do not push images, source or experiment data to a public registry without user authorization.
