from django.core import management
from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger

from datetime import datetime

from .apps import OrdertrackAppConfig


log = get_task_logger(__name__)


@shared_task
def log_action(object):
    result = {
        "timestamp": datetime.now().isoformat(),
        "id": object.get("id"),
        "name": object.get("name"),
        "model": object.get("model"),
        "action": object.get("action"),
    }
    log.info(f"Got action: {result}")
    return result


@shared_task
def create_backup():
    backup_filename = settings.BACKUP_FILE(
        OrdertrackAppConfig.name,
        f"{OrdertrackAppConfig.name}-{datetime.now():%Y-%m-%d-%H-%M}"
    )
    with open(backup_filename, "w") as f:
        management.call_command(
            "dumpdata", OrdertrackAppConfig.name, stdout=f, exclude=[])
    result = {
        "timestamp": datetime.now().isoformat(),
        "action": "database_backup",
    }
    log.info(f"Got action: {result}")
    return result
