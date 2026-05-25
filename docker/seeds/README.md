# Frappe Helpdesk seeds

Seed scripts that register the HD Ticket templates the core_app chat flow
needs (`Jira Access Request`, `Password Reset`) plus their backing Custom
Fields on `HD Ticket`.

## Automatic seeding (default)

`docker/init.sh` calls `docker/seed-templates.sh` after the site is set
up and before `bench start`. Every fresh `docker compose up` registers
both templates automatically. The seeds are idempotent — re-runs are
safe and a no-op when the templates already exist.

## Manual run (debugging only)

```bash
cd helpdesk/docker
docker compose exec frappe bash /workspace/seed-templates.sh
```

Or run a single seed manually:

```bash
docker compose exec -T -w /home/frappe/frappe-bench frappe bash -c \
  "cp /workspace/seeds/jira_access_template.py apps/frappe/frappe/jira_seed.py && \
   bench --site helpdesk.localhost execute frappe.jira_seed.execute"
```

## Where the files live

`/workspace/seeds/` inside the container is `helpdesk/docker/seeds/` on the
host (mounted via the `frappe` service's bind-mount `.:/workspace`). Each
`.py` file must exist in this directory to be picked up by
`seed-templates.sh`. The project root also has a `helpdesk/seeds/` copy —
keep them in sync; the docker-mounted copy is the one the container reads.
