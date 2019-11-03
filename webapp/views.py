from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib import messages

from webapp.models import CourseOffering, Request
from webapp.forms import RequestForm

def index(request):
    if request.user.is_authenticated:
        return redirect(reverse('request-detail', args=["cmsc12100-aut-19"]))

    context = {}

    return render(request, 'uchicago-cs/index.html', context)

@login_required
def request_detail(request, course_offering_slug, request_id = None):
    course_offering = get_object_or_404(CourseOffering, url_slug=course_offering_slug)

    if request.GET.get("request_cancelled"):
        messages.error(request, 'Your request has been cancelled.')

    force_date = request.GET.get('force_date')

    if force_date is not None:
        try:
            day = datetime.strptime(force_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Not a valid date: {}".format(force_date))
    else:
        day = datetime.now().date()


    req = None
    if request_id is not None:
        try:
            req = Request.objects.get(pk = request_id)
        except Request.DoesNotExist:
            raise Http404("No such request: {}".format(request_id))

        # Check that user owns the request that is being edited
        if not req.students.filter(pk = request.user.pk).exists():
            raise Http404("No such request: {}".format(request_id))

    context = {}
    context["course_offering"] = course_offering
    context["date"] = day

    # Check if this is a single-action POST
    if request.POST and req is not None:
        cancel = request.POST.get("cancel-request")

        if cancel == "yes":
            req.state = Request.STATE_CANCELLED
            req.save()
            return redirect(reverse('request-detail', args=[course_offering_slug]) + "?request_cancelled=yes")

    initial = {}
    form = RequestForm(request.POST or None, initial=initial, instance=req)

    context["form"] = form

    # If this is a POST request, process the request
    if request.POST:
        if form.is_valid():
            if req is None:
                req = form.save(commit=False)

                slot_dates = set([s.date for s in form.cleaned_data["slots"]])
                assert len(slot_dates) == 1

                req.date = slot_dates.pop()
                req.course_offering = course_offering
                req.save()

                req.students.add(request.user)
                form.save_m2m()
                return redirect(reverse('request-detail', args=[course_offering_slug]) + "?request_created=yes")
            else:
                form.save()

                return redirect(reverse('request-detail', args=[course_offering_slug]) + "?request_updated=yes")
        else:
            return render(request, 'uchicago-cs/request.html', context)

    if req is None:
        # We are not editing an existing request

        # Check whether the user already has an active request
        active_req = course_offering.get_active_request(request.user)

        if active_req is None:
            # If they don't, then show them a form to create a request
            slots = course_offering.slot_set.filter(date=day)

            if len(slots) > 0:
                form.fields["slots"].choices = [(s.pk, "{}".format(s.interval)) for s in slots]

                context["button_label"] = "Submit"
                context["form_action"] = reverse('request-detail', args=[course_offering_slug])
            else:
                context["form"] = None
        else:
            context["active_req"] = active_req
            context["form"] = None
    else:
        # We are viewing or editing an existing request
        slots = course_offering.slot_set.filter(date=req.date)
        form.fields["slots"].choices = [(s.pk, "{}".format(s.interval)) for s in slots]
        context["form_action"] = reverse('request-detail-id', args=[course_offering_slug, req.pk])
        context["button_label"] = "Update"

    return render(request, 'uchicago-cs/request.html', context)


