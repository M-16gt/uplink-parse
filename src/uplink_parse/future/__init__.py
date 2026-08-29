from __future__ import annotations

import uplink

from uplink_parse.core.utils.ctx import _cv_request


class request_auditor(
    uplink.hooks.RequestAuditor, uplink.decorators._BaseHandlerAnnotation
):
    pass


@request_auditor
def add_request_to_ctx(request):
    request.token_ctx = _cv_request.set(request)
    return request
