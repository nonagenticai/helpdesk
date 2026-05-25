#!/bin/bash
# Idempotent Frappe template seeder. Runs inside the `frappe` container,
# called from init.sh before `bench start`. Both seed scripts are written
# to be safe to re-run: they check existence before creating fields or
# templates.
#
# Demo-blocker #5 from core_app's docs/HANDOFF_2026-05-20.md — removes
# the manual "docker compose exec frappe bench execute ..." step that
# every fresh `docker compose up` used to require.

set -e

SEEDS_DIR=/workspace/seeds
FRAPPE_APP=/home/frappe/frappe-bench/apps/frappe/frappe
SITE=helpdesk.localhost

if [ ! -d "$SEEDS_DIR" ]; then
  echo "[seed-templates] $SEEDS_DIR not found — skipping (helpdesk/docker/seeds symlink missing?)"
  exit 0
fi

cd /home/frappe/frappe-bench

# Each seed file is copied into apps/frappe/frappe/<slug>.py so `bench
# execute` can import it as `frappe.<slug>.execute`. (The seeds dir
# itself is not on bench's Python path, hence the copy-then-execute.)
for seed in jira_access_template password_reset_template; do
  src="$SEEDS_DIR/${seed}.py"
  dst="$FRAPPE_APP/${seed}.py"
  if [ ! -f "$src" ]; then
    echo "[seed-templates] $src missing — skipping"
    continue
  fi
  cp "$src" "$dst"
  echo "[seed-templates] running frappe.${seed}.execute on $SITE"
  bench --site "$SITE" execute "frappe.${seed}.execute" || {
    echo "[seed-templates] WARNING: ${seed} failed; continuing"
  }
done

echo "[seed-templates] done"
