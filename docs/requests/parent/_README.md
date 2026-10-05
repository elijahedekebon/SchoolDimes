# Parent-app request files

VS Code REST Client files, one per parent-app area. Start with `auth.http`:
log in as the seeded parent (`parent1@schooldimes.test` / `pw123456`) and paste
the `access` token into `@token` at the top of each file. Seed ids: student
`1` (Amina), her main wallet `1`, savings wallet `2`, card `1` (`seed_demo`
creates them in this order on a fresh database; check `GET /parent/dashboard/`
if yours differ).
