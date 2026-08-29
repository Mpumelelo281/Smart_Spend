"""Single entry point for writing audit-log rows (Rule 8). Import this
everywhere an admin action or auth event happens rather than instantiating
AuditLog directly, so the "every administrative code path writes one" rule
stays enforceable by grep.
"""

from .middleware import get_audit_context
from .models import AuditLog


def log_action(action, actor=None, target=None, metadata=None, ip_address=None):
    if actor is None or ip_address is None:
        ctx_user, ctx_ip = get_audit_context()
        actor = actor or (ctx_user if ctx_user and getattr(ctx_user, "is_authenticated", False) else None)
        ip_address = ip_address or ctx_ip

    target_type = target.__class__.__name__ if target is not None else ""
    target_id = str(getattr(target, "pk", "")) if target is not None else ""

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {},
        ip_address=ip_address,
    )
