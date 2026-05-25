# Idempotent seed for the Phase-1 demo.
#
# HD Ticket Template references existing fields on HD Ticket via
# `fieldname`, so we must first add `reason` as a Custom Field on
# HD Ticket, then add it (by fieldname) to the template's `fields`
# child table.
#
# Run via:
#   docker compose exec -T -w /home/frappe/frappe-bench frappe bash -c \
#     "cp /workspace/seeds/jira_access_template.py apps/frappe/frappe/jira_seed.py && \
#      bench --site helpdesk.localhost execute frappe.jira_seed.execute"
import frappe

TEMPLATE_NAME = "Jira Access Request"
FIELD_FIELDNAME = "reason"


def _ensure_custom_field() -> None:
    if frappe.db.exists(
        "Custom Field", {"dt": "HD Ticket", "fieldname": FIELD_FIELDNAME}
    ):
        print(f"[seed] Custom Field HD Ticket.{FIELD_FIELDNAME} already present")
        return
    cf = frappe.new_doc("Custom Field")
    cf.dt = "HD Ticket"
    cf.fieldname = FIELD_FIELDNAME
    cf.label = "Reason"
    cf.fieldtype = "Long Text"
    cf.reqd = 0  # required-ness enforced via the template
    cf.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"[seed] created Custom Field HD Ticket.{FIELD_FIELDNAME}")


def _ensure_template() -> None:
    if not frappe.db.exists("HD Ticket Template", TEMPLATE_NAME):
        tmpl = frappe.new_doc("HD Ticket Template")
        tmpl.template_name = TEMPLATE_NAME
        tmpl.about = "Request access to the Jira project of your team."
        tmpl.append(
            "fields",
            {"fieldname": FIELD_FIELDNAME, "required": 1},
        )
        tmpl.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"[seed] created HD Ticket Template '{TEMPLATE_NAME}'")
        return

    tmpl = frappe.get_doc("HD Ticket Template", TEMPLATE_NAME)
    if not any(f.fieldname == FIELD_FIELDNAME for f in tmpl.fields):
        tmpl.append(
            "fields",
            {"fieldname": FIELD_FIELDNAME, "required": 1},
        )
        tmpl.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"[seed] added '{FIELD_FIELDNAME}' to '{TEMPLATE_NAME}'")
    else:
        print(f"[seed] '{TEMPLATE_NAME}' with '{FIELD_FIELDNAME}' already present")


def execute() -> None:
    _ensure_custom_field()
    _ensure_template()
