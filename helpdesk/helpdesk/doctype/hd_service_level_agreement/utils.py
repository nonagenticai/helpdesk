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


def get_sla(ticket: Document) -> frappe._dict | None:
    """
    Get the Service Level Agreement that applies to `ticket`.

    A policy applies when its condition matches and it includes the ticket's
    priority. The default policy needs no condition but is still considered last.

    :param ticket: Ticket to use (document)
    :return: Applicable SLA, or None when no policy applies
    """
    QBSla = frappe.qb.DocType(DOCTYPE)
    QBPriority = frappe.qb.DocType("HD Service Level Priority")
    now = now_datetime()
    priority = ticket.priority
    q = (
        frappe.qb.from_(QBSla)
        .select(QBSla.name, QBSla.condition, QBSla.default_sla)
        .where(QBSla.enabled == 1)
        .where(Criterion.any([QBSla.start_date.isnull(), QBSla.start_date <= now]))
        .where(Criterion.any([QBSla.end_date.isnull(), QBSla.end_date >= now]))
        .orderby(QBSla.default_sla)  # the Default SLA is considered last
        .orderby(QBSla.rank == 0)  # unranked sorts after ranked
        .orderby(QBSla.rank)
        .orderby(QBSla.creation)
    )
    if priority:
        q = (
            q.join(QBPriority, JoinType.inner)
            .on(QBPriority.parent == QBSla.name)
            .where(QBPriority.priority == priority)
        )
    context = None
    for sla in q.run(as_dict=True):
        if sla.default_sla:
            return sla
        if not sla.condition:
            continue  # a blank condition is not a false positive
        context = context or get_context(ticket)  # serialises the ticket, build once
        if frappe.safe_eval(sla.condition, None, context):
            return sla
    return None


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
