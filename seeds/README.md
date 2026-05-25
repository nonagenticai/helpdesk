# Frappe Helpdesk seeds

Seed scripts that run inside the `frappe` container via `bench execute`.

## Run the Jira-access template seed

```bash
cd helpdesk/docker
docker compose exec frappe bench --site helpdesk.localhost execute \
    seeds.jira_access_template.execute
```

Idempotent — safe to re-run.

The `seeds/` directory is symlinked into the container at `/workspace/seeds`
via the `helpdesk/docker/` bind-mount. Symlink to create:

```bash
ln -s ../seeds /Users/georgedekker/Movies/RaiseMyTickets/helpdesk/docker/seeds
```
