import logging
from pathlib import Path
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.http import HttpResponse

from ..models import Confirmation, ConfirmationItem, Supplier, Product, Client
from ..forms.confirmations import (
    ConfirmationModelForm,
    EditConfirmationModelForm,
    ViewConfirmationModelForm,
    ViewItemFormSet,
    EditItemFormSet)
from ..forms.uploadfile import UploadConfirmationForm

template_path = Path("ordertrack_app") / "confirmations"

log = logging.getLogger(__name__)


def confirmations(request):
    confirmations_list = Confirmation.objects.all(
    ).order_by("-confirmation_date", "name")
    context = {
        "confirmations": confirmations_list,
    }
    return render(request, template_path/"confirmations.html", context=context)


def view_confirmation(request, confirmation_id):
    confirmation = get_object_or_404(Confirmation, id=confirmation_id)
    confirmation_items = ConfirmationItem.objects.filter(
        confirmation_id=confirmation_id)  # .order_by("-client_id")
    form = ViewConfirmationModelForm(instance=confirmation)
    formset = ViewItemFormSet(queryset=confirmation_items,
                              form_kwargs={'confirmation': confirmation})
    context = {
        'conformation_form': form,
        'formset': formset,
        'view_conformation': True,
    }
    return render(request, template_path/"viewconfirmation.html", context=context)


def edit_confirmation(request, confirmation_id):
    confirmation = get_object_or_404(Confirmation, id=confirmation_id)
    confirmation_items = ConfirmationItem.objects.filter(
        confirmation_id=confirmation_id)  # .order_by("-client_id")

    if request.method == 'POST':
        if 'save' in request.POST:
            form = EditConfirmationModelForm(
                request.POST, instance=confirmation)
            formset = EditItemFormSet(
                request.POST, form_kwargs={'confirmation': confirmation})
            if form.is_valid() and formset.is_valid():
                form.save()
                formset.save(commit=False)
                for obj in formset.deleted_objects:
                    obj.delete()
                formset.save()
                return redirect(reverse('viewconfirmation', args=[form.instance.id]))
            else:
                context = {
                    'conformation_form': form,
                    'formset': formset,
                }
                return render(request, template_path/"viewconfirmation.html", context=context)

    form = EditConfirmationModelForm(instance=confirmation)
    formset = EditItemFormSet(queryset=confirmation_items,
                              form_kwargs={'confirmation': confirmation})
    context = {
        'conformation_form': form,
        'formset': formset,
    }
    return render(request, template_path/"viewconfirmation.html", context=context)


def delete_confirmation(request, confirmation_id):
    if request.method == 'POST':
        confirmation = Confirmation.objects.get(id=confirmation_id)
        confirmation.delete()
    return redirect(reverse('confirmations'))


def new_confirmation(request):
    if request.method == 'POST':
        form = ConfirmationModelForm(request.POST)
        loadform = UploadConfirmationForm(request.POST, request.FILES)
        context = {'form': form, 'loadform': loadform,
                   'title': 'New Confirmation'}
        action = request.POST.get('action')
        if form.is_valid():
            if action == 'preview':
                if uploaded_file := request.FILES.get('file'):
                    try:
                        supplier = form.cleaned_data["supplier"]
                        # brands = form.cleaned_data.get("brand", [])
                        confirmation_code, confirmation_data = loadform.load_excel_confirmation(
                            uploaded_file, supplier=supplier)
                        current_values = {
                            'order': request.POST.getlist('order'),
                        }
                        form.instance.confirmation_code = confirmation_code
                        form.save(commit=False)
                        context['form'] = ConfirmationModelForm(
                            instance=form.instance,
                            initial=current_values)
                        request.session['confirmation_data_json'] = loadform.data_json(
                            confirmation_data)
                        context['confirmationdata'] = confirmation_data
                        context['add_confirmation_disabled'] = False
                    except Exception as e:
                        context['confirmationdata'] = f'Cannot upload data from {uploaded_file}, {e}'
                        context['add_confirmation_disabled'] = True
                else:
                    context['confirmationdata'] = f'No file selected. Choose file'
                    context['add_confirmation_disabled'] = True
                return render(request, template_path/"newconfirmation.html", context)
            elif action == 'add':
                if form.is_valid() and loadform.is_valid():
                    confirmation_data_json = json.loads(
                        request.session.get('confirmation_data_json'))
                    try:
                        with transaction.atomic():
                            confirmation = form.save(commit=False)
                            confirmation.save()
                            form.save_m2m()
                            loadform.save_confirmation_items(
                                confirmation_data_json=confirmation_data_json, confirmation=confirmation)
                    except Exception as e:
                        context['confirmationdata'] = f'Cannot save data, {e}'
                        context['add_confirmation_disabled'] = True
                        return render(request, template_path/"newconfirmation.html", context)
                    del request.session['confirmation_data_json']
                    return redirect(reverse('viewconfirmation', args=[form.instance.id]))

    else:
        form = ConfirmationModelForm(
            initial={'supplier': Supplier.objects.get(id="T00016")})
        loadform = UploadConfirmationForm()
        context = {'form': form, 'loadform': loadform,
                   'title': 'New Confirmation', 'add_confirmation_disabled': True}

    return render(request, template_path/"newconfirmation.html", context)


def export_to_excel(request, confirmation_id):
    confirmation = Confirmation.objects.get(id=confirmation_id)
    confirmation_items = ConfirmationItem.objects.filter(
        confirmation_id=confirmation_id).order_by("-client_id")
    formset = ViewItemFormSet(queryset=confirmation_items, form_kwargs={
                              'confirmation': confirmation})
    excel_file = formset.export_to_excel()
    if excel_file:
        excel_response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': 'attachment; filename="data.xlsx"'
            }
        )
        return excel_response
    return HttpResponse()
