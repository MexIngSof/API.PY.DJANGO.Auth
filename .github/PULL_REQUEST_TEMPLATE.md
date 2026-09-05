## Scope

- [ ] This PR changes one clear responsibility in this repository.
- [ ] `service-metadata.yml` still matches framework policy `2026.09.1`.

## Validation

- [ ] General/policy gates pass.
- [ ] Language tests/checks applicable to this change pass.
- [ ] Docker/build validation passes when runtime or dependencies changed.
- [ ] No `latest`, secrets, credentials or private `.env` values were added.

## Contracts and data

- [ ] Public contract impact was reviewed.
- [ ] Consumers are included in the release plan if compatibility changes.
- [ ] Migrations are expand/contract compatible when applicable.

## Delivery

- [ ] Deployment remains service-owned and uses `--no-deps`.
- [ ] Health/smoke expectations are documented.
- [ ] Rollback impact is documented; image/runtime rollback does not imply data rollback.
- [ ] Documentation/ADR was updated when behavior or architecture changed.

## External requirements

List only requirements that genuinely need external admin, credentials or an environment. Do not mark unexecuted validation as PASS.
