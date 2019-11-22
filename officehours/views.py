from datetime import datetime, time
from collections import OrderedDict
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib import messages
import django_tables2

from officehours.models import CourseOffering, Request, Slot
from officehours.forms import RequestForm
from officehours.tables import RequestTable
from django.utils import timezone


def index(request):
    if request.user.is_authenticated:
        return redirect(reverse('my-request', args=["cmsc12100-aut-19"]))

    context = {}

    return render(request, 'uchicago-cs/index.html', context)

@login_required
def my_request(request, course_offering_slug):
    if request.GET.get("request_updated"):
        messages.success(request, 'Your request has been updated.')

    if request.GET.get("request_created"):
        messages.success(request, 'Your request has been created.')

    if request.GET.get("request_cancelled"):
        messages.error(request, 'Your request has been cancelled. You can make a new request below.')

    course_offering = get_object_or_404(CourseOffering, url_slug=course_offering_slug)
    user_is_server = course_offering.is_server(request.user)

    context = {}
    context["course_offering"] = course_offering
    context["user_is_server"] = user_is_server

    active_req = request.user.get_active_request(course_offering)

    if request.POST and active_req is None:
        # Check if this is the creation of a new request

        form = RequestForm(request.POST)

        if form.is_valid():
            active_req = form.save(commit=False)

            slot_dates = set([s.date for s in form.cleaned_data["slots"]])
            assert len(slot_dates) == 1

            active_req.date = slot_dates.pop()
            active_req.course_offering = course_offering
            active_req.student = request.user
            active_req.save()

            active_req.make_active()

            form.save_m2m()

    # We're done modifying/creating the request. After this point,
    # it's all display.

    context["active_req"] = active_req

    if active_req is None:
        # There is no active request, so we show the form to create one

        # Allow instructors/TAs to choose arbitrary dates
        force_date = request.GET.get('force_date')

        if user_is_server and force_date is not None:
            try:
                day = datetime.strptime(force_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Not a valid date: {}".format(force_date))
        else:
            day = timezone.localtime(timezone.now()).date()

        context["date"] = day

        # Are there slots available on the selected day?
        slots = course_offering.slot_set.filter(date=day).order_by("start_time")

        if len(slots) > 0:
            form = RequestForm()
            form.fields["slots"].choices = [(s.pk, "{}".format(s.interval)) for s in slots]

            context["form"] = form
            context["button_label"] = "Submit"
            context["form_action"] = reverse('my-request', args=[course_offering.url_slug])
        else:
            context["form"] = None

    # If there is an active request, then my-request.html will display it.

    return render(request, 'uchicago-cs/my-request.html', context)


@login_required
def request_detail(request, course_offering_slug, request_id):
    course_offering = get_object_or_404(CourseOffering, url_slug=course_offering_slug)
    user_is_server = course_offering.is_server(request.user)

    context = {}
    context["course_offering"] = course_offering
    context["user_is_server"] = user_is_server

    try:
        req = Request.objects.get(pk = request_id)
    except Request.DoesNotExist:
        raise Http404("No such request: {}".format(request_id))

    # Check that user is a server for this course or owns the request that is being edited
    if not (user_is_server or req.student == request.user):
        raise Http404("No such request: {}".format(request_id))

    context["req"] = req

    # Check if this is a POST making a specific modification
    if request.POST:
        update_type = request.POST.get("update-type")
        next_page = request.POST.get("next-page")

        if update_type == "cancel":
            req.cancel()
            return redirect(next_page + "?request_cancelled=yes")
        elif update_type == "schedule" and user_is_server:
            slot_pk = request.POST.get("slot")

            try:
                slot = req.slots.get(pk=slot_pk)
                req.schedule(slot)
                email_success = req.send_notification_email("uchicago-cs/emails/scheduled.txt", cc_users=[request.user])
                if email_success:
                    return redirect(next_page + "?request_scheduled=yes")
                else:
                    return redirect(next_page + "?request_scheduled=yes_noemail")
            except Slot.DoesNotExist:
                return redirect(next_page + "?request_scheduled=no")
        elif update_type == "start-service" and user_is_server:
            req.start_service(server=request.user)
            return redirect(next_page + "?request_started=yes")
        elif update_type == "complete-service" and user_is_server:
            req.complete_service()
            return redirect(next_page + "?request_completed=yes")
        elif update_type == "no-show" and user_is_server:
            req.no_show()
            return redirect(next_page + "?request_noshow=yes")
        elif update_type == "could-not-see" and user_is_server:
            req.could_not_see()
            email_success = req.send_notification_email("uchicago-cs/emails/could-not-see.txt")
            if email_success:
                return redirect(next_page + "?request_couldnotsee=yes")
            else:
                return redirect(next_page + "?request_couldnotsee=yes_noemail")
            return redirect(next_page + "?request_couldnotsee=yes")
        elif update_type is not None:
            return redirect("/")



    initial = {}
    form = RequestForm(request.POST or None, initial=initial, instance=req)

    context["form"] = form

    # If this is a POST request, process the request
    if request.POST:
        if form.is_valid():
            form.save()

            if req.student == request.user:
                return redirect(reverse('my-request', args=[course_offering_slug]) + "?request_updated=yes")
            elif user_is_server:
                return redirect(reverse('requests-all', args=[course_offering_slug]))
            else:
                return redirect(reverse('request-detail', args=[course_offering_slug, req.pk]))
        else:
            return render(request, 'uchicago-cs/request.html', context)

    # We are viewing or editing an existing request
    slots = course_offering.slot_set.filter(date=req.date)
    form.fields["slots"].choices = [(s.pk, "{}".format(s.interval)) for s in slots]
    context["form_action"] = reverse('request-detail', args=[course_offering_slug, req.pk])
    context["button_label"] = "Update"

    return render(request, 'uchicago-cs/request.html', context)



def requests_today(request, course_offering_slug):
    course_offering = get_object_or_404(CourseOffering, url_slug=course_offering_slug)
    user_is_server = course_offering.is_server(request.user)

    if not user_is_server:
        raise Http404()

    context = {}
    context["course_offering"] = course_offering
    context["user_is_server"] = user_is_server

    force_date = request.GET.get('force_date')

    if force_date is not None:
        try:
            day = datetime.strptime(force_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Not a valid date: {}".format(force_date))
    else:
        day = timezone.localtime(timezone.now()).date()

    current_slot = Slot.get_current_slot(course_offering)

    today_requests = course_offering.request_set.filter(date=day)

    requests_pending_today = sorted(today_requests.filter(state=Request.STATE_PENDING).order_by("created_at"),
                                    key=lambda x: x.next_available_slot.start_time if x.next_available_slot else time(23, 59))


    context["requests_pending_today"] = requests_pending_today
    context["requests_pending_now"] = today_requests.filter(state=Request.STATE_PENDING, slots__in=[current_slot]).order_by("created_at")

    requests_scheduled = sorted(today_requests.filter(state=Request.STATE_SCHEDULED, actual_slot__isnull=False),
                                key=lambda x: x.actual_slot.start_time)

    context["requests_scheduled"] = requests_scheduled
    context["requests_inprogress"] = today_requests.filter(state=Request.STATE_INPROGRESS)
    context["requests_completed"] = today_requests.filter(state=Request.STATE_COMPLETED)

    return render(request, 'uchicago-cs/requests-today.html', context)


def requests_all(request, course_offering_slug):
    course_offering = get_object_or_404(CourseOffering, url_slug=course_offering_slug)
    user_is_server = course_offering.is_server(request.user)

    if not user_is_server:
        raise Http404()

    context = {}
    context["course_offering"] = course_offering
    context["user_is_server"] = user_is_server

    all_requests = course_offering.request_set.all()

    table_all = RequestTable(all_requests)
    django_tables2.RequestConfig(request).configure(table_all)
    context["table_all"] = table_all

    return render(request, 'uchicago-cs/requests-all.html', context)


@login_required
def status(request, course_offering_slug):
    course_offering = get_object_or_404(CourseOffering, url_slug=course_offering_slug)
    user_is_server = course_offering.is_server(request.user)

    # Allow instructors/TAs to choose arbitrary dates
    force_date = request.GET.get('force_date')

    if user_is_server and force_date is not None:
        try:
            day = datetime.strptime(force_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Not a valid date: {}".format(force_date))
    else:
        day = timezone.localtime(timezone.now()).date()

    context = {}
    context["course_offering"] = course_offering
    context["user_is_server"] = user_is_server
    context["date"] = day

    # Are there slots available on the selected day?
    slots = course_offering.slot_set.filter(date=day).order_by("start_time")

    if len(slots) == 0:
        context["slot_requests"] = None
    else:
        slot_requests = OrderedDict()
        for slot in slots:
            slot_requests[slot] ={"pending":0, "scheduled":0, "inprogress":0, "completed": 0}

        today_requests = course_offering.request_set.filter(date=day)

        total_pending = 0

        for req in today_requests:
            if req.state == Request.STATE_PENDING:
                next_available_slot = req.next_available_slot
                if next_available_slot is not None:
                    slot_requests[next_available_slot]["pending"] += 1
                    total_pending += 1
            elif req.state == Request.STATE_SCHEDULED:
                req_slot = req.actual_slot
                slot_requests[req_slot]["scheduled"] += 1
            elif req.state == Request.STATE_INPROGRESS:
                req_slot = req.actual_slot
                slot_requests[req_slot]["inprogress"] += 1
            elif req.state == Request.STATE_COMPLETED:
                req_slot = req.actual_slot
                slot_requests[req_slot]["completed"] += 1

        print(slot_requests)
        context["total_pending"] = total_pending
        context["slot_requests"] = slot_requests

    return render(request, 'uchicago-cs/status.html', context)