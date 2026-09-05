"""
Entry point for the Function App. Event Grid calls this directly — no
intermediate queue. Retries and dead-lettering are handled by the Event Grid
subscription itself (max-delivery-attempts / deadletter-endpoint), not by
this code.
"""
import logging

import azure.functions as func

from composition import build_use_case
from domain.models import BlobEvent, ChangeType

app = func.FunctionApp()


@app.function_name(name="blob_event_handler")
@app.event_grid_trigger(arg_name="event")
def blob_event_handler(event: func.EventGridEvent) -> None:
    data = event.get_json()
    change_type = (
        ChangeType.DELETED
        if event.event_type.endswith("BlobDeleted")
        else ChangeType.CREATED_OR_UPDATED
    )
    blob_event = BlobEvent(blob_url=data["url"], change_type=change_type)

    # execute() raises on failure — that's what tells Azure Functions this
    # invocation failed, so Event Grid's own retry policy kicks in.
    result = build_use_case().execute(blob_event)
    logging.info("Processed %s -> %s", blob_event.blob_url, result.status)