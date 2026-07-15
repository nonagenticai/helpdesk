from datetime import time, timedelta

import frappe
from frappe.model.document import Document
from frappe.query_builder import JoinType
from frappe.utils import now_datetime, to_timedelta
from pypika import Criterion

from helpdesk.utils import get_context


def to_working_timedelta(value):
    """
    Normalize a Frappe Time field value to a ``datetime.timedelta``.

    Frappe returns Time columns with a driver-dependent Python type: MariaDB
    yields ``datetime.timedelta`` while Postgres yields ``datetime.time``. The
    working-hours/SLA math compares against timedeltas, so normalize both (and
    string values) to timedelta for engine-agnostic behaviour.
    """
    if value is None:
        return timedelta(0)
    if isinstance(value, timedelta):
        return value
    if isinstance(value, time):
        return timedelta(hours=value.hour, minutes=value.minute, seconds=value.second)
    return to_timedelta(str(value))

DOCTYPE = "HD Service Level Agreement"


def get_sla(ticket: Document) -> Document:
    """
    Get Service Level Agreement for `ticket`

    :param doc: Ticket to use
    :return: Applicable SLA
    """
    QBSla = frappe.qb.DocType(DOCTYPE)
    QBPriority = frappe.qb.DocType("HD Service Level Priority")
    now = now_datetime()
    priority = ticket.priority
    q = (
        frappe.qb.from_(QBSla)
        .select(QBSla.name, QBSla.condition)
        .where(QBSla.enabled == 1)
        .where(QBSla.default_sla == 0)
        .where(Criterion.any([QBSla.start_date.isnull(), QBSla.start_date <= now]))
        .where(Criterion.any([QBSla.end_date.isnull(), QBSla.end_date >= now]))
    )
    if priority:
        q = (
            q.join(QBPriority, JoinType.inner)
            .on(QBPriority.parent == QBSla.name)
            .where(QBPriority.priority == priority)
        )
    sla_list = q.run(as_dict=True)
    res = None
    for sla in sla_list:
        cond = sla.get("condition")
        if not cond or frappe.safe_eval(cond, None, get_context(ticket)):
            res = sla
            break
    return res or get_default()


def get_default() -> Document:
    """
    Get default Service Level Agreement

    :return: Default SLA
    """
    return frappe.get_last_doc(
        DOCTYPE,
        filters={
            "enabled": True,
            "default_sla": True,
        },
    )


def convert_to_seconds(time):
    """
    Convert a Frappe Time field value to seconds-since-midnight.

    Frappe returns Time columns with a driver-dependent Python type: MariaDB
    yields ``datetime.timedelta`` (has ``.total_seconds()``) while Postgres
    yields ``datetime.time`` (has ``.hour``/``.minute``/``.second``). Handle both
    so SLA time math is engine-agnostic.

    :param time: Time value (datetime.timedelta or datetime.time) or falsy
    :return: Time in seconds
    """
    if not time:
        return 0
    if hasattr(time, "total_seconds"):  # datetime.timedelta (MariaDB)
        return int(time.total_seconds())
    return time.hour * 3600 + time.minute * 60 + time.second  # datetime.time (Postgres)
