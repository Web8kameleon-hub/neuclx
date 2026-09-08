# NeuCLX TODO

Ky dokument regjistron punën e mbetur pa ndryshuar skedarët pending në PC-në e zyrës.

## Sinkronizimi dhe kontrolli

- [ ] Sinkronizo skedarët pending nga PC-ja e zyrës.
- [ ] Kontrollo diferencat me `main` pa mbishkruar ndryshime.
- [ ] Inventarizo skedarët: të rinj, të modifikuar, dublikatë dhe konfliktualë.
- [ ] Klasifiko evidencën: `measured`, `computed`, `declared`, `unavailable`.

## Korrigjimet teknike

- [ ] Korrigjo tri mospërputhjet SHA-256 në manifest.
- [ ] Plotëso modulin që mungon `neuclx.data`.
- [ ] Zëvendëso pseudo-hash-in e `RepoBridge` me SHA-256 real.
- [ ] Mos regjistro faktet e përdoruesit si `computed`; ruaji si `declared` deri në verifikim.
- [ ] Dallo qartë komponentët realë nga funksionet `not_implemented`.

## Testimi dhe verifikimi

- [ ] Përdor vetëm një test runner ose siguro që të gjitha testet ekzekutohen.
- [ ] Testo memory SQLite, bridge, agjentët, API-n dhe UI-n.
- [ ] Ekzekuto kontrollin e provenance dhe deduplikimit.
- [ ] Ekzekuto benchmark-et dhe verifiko SLI/SLO.
- [ ] Kërko zero gabime, zero konflikte dhe zero dublikime.
- [ ] Bëj CI/CD plotësisht green.

## Paketat dhe release-et

- [ ] Verifiko paketat kandidate Python, npm dhe Rust pa i publikuar.
- [ ] Gjenero dokumentet dhe artifact-et shoqëruese.
- [ ] Mbro degën `main` me status checks të detyrueshme.
- [ ] Nënshkruaj commit-et dhe release-et.
- [ ] Publiko paketat vetëm pasi maturity gate ta deklarojë produktin të pjekur.
