# Idempotent seed for the password-reset intent (Phase-1 follow-up).
#
# HD Ticket Template references existing fields on HD Ticket via
# `fieldname`, so we first add `account` and `reason` as Custom Fields
# on HD Ticket, then add them (by fieldname) to the template.
#
# Run via:
#   docker compose exec -T -w /home/frappe/frappe-bench frappe bash -c \
#     "cp /workspace/seeds/password_reset_template.py apps/frappe/frappe/pwd_seed.py && \
#      bench --site helpdesk.localhost execute frappe.pwd_seed.execute"
import frappe

TEMPLATE_NAME = "Password Reset"
FIELDS = (
    {"fieldname": "account", "label": "Account", "fieldtype": "Data"},
    {"fieldname": "reason", "label": "Reason", "fieldtype": "Long Text"},
)


def _ensure_custom_field(field: dict) -> None:
    if frappe.db.exists("Custom Field", {"dt": "HD Ticket", "fieldname": field["fieldname"]}):
        print(f"[seed] Custom Field HD Ticket.{field['fieldname']} already present")
        return
    cf = frappe.new_doc("Custom Field")
    cf.dt = "HD Ticket"
    cf.fieldname = field["fieldname"]
    cf.label = field["label"]
    cf.fieldtype = field["fieldtype"]
    cf.reqd = 0
    cf.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"[seed] created Custom Field HD Ticket.{field['fieldname']}")


def _ensure_template() -> None:
    if not frappe.db.exists("HD Ticket Template", TEMPLATE_NAME):
        tmpl = frappe.new_doc("HD Ticket Template")
        tmpl.template_name = TEMPLATE_NAME
        tmpl.about = "Reset an internal account password."
        for f in FIELDS:
            tmpl.append("fields", {"fieldname": f["fieldname"], "required": 1})
        tmpl.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"[seed] created HD Ticket Template '{TEMPLATE_NAME}'")
        return

    tmpl = frappe.get_doc("HD Ticket Template", TEMPLATE_NAME)
    existing = {f.fieldname for f in tmpl.fields}
    changed = False
    for f in FIELDS:
        if f["fieldname"] not in existing:
            tmpl.append("fields", {"fieldname": f["fieldname"], "required": 1})
            changed = True
    if changed:
        tmpl.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"[seed] updated '{TEMPLATE_NAME}'")
    else:
        print(f"[seed] '{TEMPLATE_NAME}' already present")


def execute() -> None:
    for f in FIELDS:
        _ensure_custom_field(f)
    _ensure_template()
