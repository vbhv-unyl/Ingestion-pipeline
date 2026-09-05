import base64
import json
import logging
from dataclasses import asdict

import azure.durable_functions as df
import azure.functions as func

from composition import build_use_case
from domain.models import BlobEvent, ChangeType

app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.queue_trigger(arg_name="msg", queue_name="blob-events", connection="AzureWebJobsStorage")
@app.durable_client_input(client_name="client")
async def blob_event_starter(msg: func.QueueMessage, client: df.DurableOrchestrationClient):
    event = _parse_event_grid_message(msg.get_body())
    change_type = (
        ChangeType.DELETED if event.get("eventType", "").endswith("BlobDeleted")
        else ChangeType.CREATED_OR_UPDATED
    )
    normalized = {"blob_url": event["data"]["url"], "change_type": change_type.value}

    instance_id = await client.start_new("ingestion_orchestrator", client_input=normalized)
    logging.info("Started orchestration %s for %s", instance_id, normalized["blob_url"])


@app.orchestration_trigger(context_name="context")
def ingestion_orchestrator(context: df.DurableOrchestrationContext):
    event_dict = context.get_input()
    retry_options = df.RetryOptions(first_retry_interval_in_milliseconds=5000, max_number_of_attempts=3)
    result = yield context.call_activity_with_retry("handle_blob_event", retry_options, event_dict)
    return result


@app.activity_trigger(input_name="eventDict")
def handle_blob_event(eventDict: dict) -> dict:
    event = BlobEvent(blob_url=eventDict["blob_url"], change_type=ChangeType(eventDict["change_type"]))
    result = build_use_case().execute(event)
    return asdict(result)


def _parse_event_grid_message(raw: bytes) -> dict:
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Event Grid delivers to Storage Queues as base64 in some configurations.
        event = json.loads(base64.b64decode(raw).decode("utf-8"))
    return event[0] if isinstance(event, list) else event