import logging
from pathlib import Path
from django.shortcuts import render, get_list_or_404


from ..models import Confirmation, ConfirmationItem

template_path = Path("ordertrack_app") / "confirmations"
log = logging.getLogger(__name__)


def confirmations(request):
    confirmations_list = Confirmation.objects.all().order_by("-confirmation_date")
    context = {
        "confirmations": confirmations_list,
    }
    return render(request, template_path/"confirmations.html", context=context)


def confirmationitems(request, confirmation_id):
    confirmation_items = get_list_or_404(
        ConfirmationItem, confirmation_id=confirmation_id)
    context = {
        "confirmationitems": confirmation_items
    }
    return render(request, template_path/"confirmationitems.html", context=context)
