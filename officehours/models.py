import os
from datetime import timedelta
from smtplib import SMTPException

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.template.loader import get_template
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage

class User(AbstractUser):
    active_requests = models.ManyToManyField("CourseOffering",
                                             through="ActiveRequest",
                                             blank=True)

    def get_active_request(self, course_offering):
        try:
            active_req = ActiveRequest.objects.get(course_offering=course_offering,
                                                   user=self)
            req = active_req.request
        except ActiveRequest.DoesNotExist:
            req = None

        return req


class Quarter(models.Model):
    ais_num = models.PositiveIntegerField(primary_key=True)
    year = models.PositiveIntegerField()
    quarter = models.CharField(max_length=3, choices = [("aut", "Autumn"),
                                                        ("win", "Winter"),
                                                        ("spr", "Spring"),
                                                        ("sum", "Summer")])

    class Meta:
        unique_together = (("year", "quarter"),)

    def __str__(self):
        return "{} {}".format(self.get_quarter_display(), self.year)

    @property
    def academic_year(self):
        if self.quarter in ("sum", "aut"):
            return "{}/{:02d}".format(self.year, (self.year % 100) + 1)
        elif self.quarter in ("win", "spr"):
            return "{}/{:02d}".format(self.year - 1, (self.year % 100))


class Course(models.Model):
    ais_num = models.PositiveIntegerField(primary_key=True)
    subject = models.CharField(max_length=4)
    catalog_code = models.IntegerField(validators=[MinValueValidator(10000),
                                                   MaxValueValidator(99999)])
    name = models.CharField(max_length=256)

    def __str__(self):
        return "{} {} - {} ({})".format(self.subject, self.catalog_code, self.name, self.ais_num)


class CourseOffering(models.Model):
    STATE_OPEN = 10
    STATE_CLOSED = 20

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)
    state = models.PositiveIntegerField(choices = [(STATE_OPEN,   "Open"),
                                                   (STATE_CLOSED, "Closed")],
                                        default = STATE_CLOSED)

    url_slug = models.CharField(max_length=256, unique=True)

    servers = models.ManyToManyField(User, blank=True)

    class Meta:
        unique_together = (("course", "quarter"),)

    def __str__(self):
        return "{} {} - {} ({})".format(self.subject, self.catalog_code, self.name, self.quarter)

    @property
    def ais_num(self):
        return self.course.ais_num

    @property
    def subject(self):
        return self.course.subject

    @property
    def catalog_code(self):
        return self.course.catalog_code

    @property
    def name(self):
        return self.course.name

    @property
    def catalog(self):
        return "{} {}".format(self.subject, self.catalog_code)

    @property
    def catalog_quarter(self):
        return "{} ({})".format(self.catalog, self.quarter)

    def get_active_request(self, user):
        try:
            active_req = ActiveRequest.objects.get(course_offering=self,
                                                   user=user)
            req = active_req.request
        except ActiveRequest.DoesNotExist:
            req = None

        return req

    def is_server(self, user):
        return self.servers.filter(pk = user.pk).exists()


class Slot(models.Model):
    SLOT_ONLINE = 10
    SLOT_INPERSON = 20

    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=64, null=True, blank=True)

    format = models.PositiveIntegerField(choices = [(SLOT_ONLINE, "Online"),
                                                    (SLOT_INPERSON, "In-person")])

    def __str__(self):
        slot_str = "{} ({})".format(self.date, self.interval)
        if self.format == Slot.SLOT_ONLINE:
            slot_str += " [Online]"
        return slot_str

    @property
    def interval(self):
        start = self.start_time.strftime("%I:%M %p")
        end = self.end_time.strftime("%I:%M %p")
        return "{} - {}".format(start, end)

    @property
    def online(self):
        return self.format == Slot.SLOT_ONLINE

    @staticmethod
    def get_next_slots(course_offering, hours):
        now = timezone.localtime(timezone.now())

        slots = Slot.objects.filter(course_offering=course_offering,
                                    date=now.date(),
                                    end_time__lte=(now + timedelta(hours=hours)).time())

        return slots


class Request(models.Model):
    STATE_PENDING = 10
    STATE_SCHEDULED = 20
    STATE_INPROGRESS = 30
    STATE_COMPLETED = 40
    STATE_NOSHOW = 50
    STATE_COULDNOTSEE = 60
    STATE_CANCELLED = 70
    STATE_INVALID = 80

    ACTIVE_STATES = (STATE_PENDING, STATE_SCHEDULED, STATE_INPROGRESS)

    TYPE_REGULAR = 10
    TYPE_QUICK = 20

    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    additional_students = models.ManyToManyField(User, related_name="additional_requests", blank=True)
    server = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="assigned_requests")
    date = models.DateField()

    slots = models.ManyToManyField(Slot)
    actual_slot = models.ForeignKey(Slot, on_delete=models.CASCADE, blank=True, null=True, related_name="assigned_slot")

    created_at = models.DateTimeField(default=timezone.now)
    service_start_time = models.TimeField(blank=True, null=True)
    service_end_time = models.TimeField(blank=True, null=True)

    state = models.PositiveIntegerField(choices = [(STATE_PENDING,     "Pending"),
                                                   (STATE_SCHEDULED,   "Scheduled"),
                                                   (STATE_INPROGRESS,  "In Progress"),
                                                   (STATE_COMPLETED,   "Completed"),
                                                   (STATE_NOSHOW,      "No-show"),
                                                   (STATE_COULDNOTSEE, "Could not schedule"),
                                                   (STATE_CANCELLED,   "Cancelled"),
                                                   (STATE_INVALID,     "Invalid"),
                                                   ],
                                        default = STATE_PENDING)

    type = models.PositiveIntegerField(choices = [(TYPE_REGULAR, "Regular"),
                                                  (TYPE_QUICK, "Quick Question")
                                                 ],
                                        default = TYPE_REGULAR)

    zoom_url = models.URLField(null=True, blank=True)

    description = models.TextField()

    def __get_active(self):
        try:
            active_req = ActiveRequest.objects.get(course_offering = self.course_offering,
                                                   user = self.student)
        except ActiveRequest.DoesNotExist:
            active_req = None

        return active_req

    @property
    def is_active(self):
        active_req = self.__get_active()

        return active_req is not None and active_req.request == self

    @property
    def is_pending(self):
        return self.state == Request.STATE_PENDING

    @property
    def is_scheduled(self):
        return self.state == Request.STATE_SCHEDULED

    @property
    def is_inprogress(self):
        return self.state == Request.STATE_INPROGRESS

    @property
    def is_scheduled_online(self):
        if self.actual_slot is None:
            return False
        else:
            return self.actual_slot.format == Slot.SLOT_ONLINE

    @property
    def ordered_slots(self):
        return self.slots.all().order_by("start_time", "-format")

    @property
    def next_available_slots(self):
        now = timezone.localtime(timezone.now())

        next_slot = self.slots.filter(end_time__gt=now.time()).order_by("start_time").first()

        if next_slot:
            # There could be other slots (e.g., with a different format) with the same times
            next_slots = self.slots.filter(date=next_slot.date,
                                           start_time=next_slot.start_time,
                                           end_time=next_slot.end_time)
        else:
            next_slots = next_slot

        return next_slots

    @property
    def priority(self):
        q = self.course_offering.request_set
        previous_request = q.filter(student=self.student) \
                            .exclude(state__in=(Request.STATE_PENDING, Request.STATE_CANCELLED, Request.STATE_NOSHOW)) \
                            .order_by("-created_at") \
                            .first()

        if previous_request is not None and previous_request.state == Request.STATE_COULDNOTSEE:
            return True
        else:
            return False

    def get_state_class(self):
        if self.state in (Request.STATE_PENDING,):
            return "btn-warning"
        elif self.state in (Request.STATE_SCHEDULED, Request.STATE_INPROGRESS):
            return "btn-success"
        elif self.state in (Request.STATE_COMPLETED,):
            return "btn-info"
        elif self.state in (Request.STATE_NOSHOW, Request.STATE_COULDNOTSEE, Request.STATE_CANCELLED, Request.STATE_INVALID):
            return "btn-danger"
        else:
            return "btn-info"

    @property
    def get_students_display(self):
        student = "{} {}".format(self.student.first_name, self.student.last_name)

        if self.additional_students.exists():
            l = ["{} {}".format(s.first_name, s.last_name) for s in self.additional_students.all()]
            s = " (and {})".format(", ".join(l))
        else:
            s = ""

        return student + s

    @property
    def get_accordion_display(self):
        """Produces string summary displayed on 'accordions' in Today's Request"""

        created_at = timezone.localtime(self.created_at)
        now = timezone.localtime(timezone.now())

        next_str = ""
        if self.state == Request.STATE_PENDING:
            next_slots = self.next_available_slots

            if next_slots is not None:
                next_slot = next_slots.first()
                if next_slot.date == now.date() and next_slot.start_time <= now.time() <= next_slot.end_time:
                    next_str = "(Available NOW)"
                else:
                    next_str = "(Earliest availability: {})".format(next_slot.interval)
            else:
                next_str = "(No availability)"

        if self.actual_slot is not None:
            actual = " @ {}".format(self.actual_slot.interval)
        else:
            actual = ""

        if self.state == Request.STATE_PENDING and self.priority:
            priority = "<strong style='color: red'>PRIORITY</strong>"
        else:
            priority = ""

        if self.type == Request.TYPE_QUICK:
            quick = "<strong style='color: green'>QUICK</strong>"
        else:
            quick = ""

        s = "[{}] {} {} {} {} {}".format(created_at.strftime("%I:%M:%S %p"), self.get_students_display, actual, next_str, quick, priority)

        return mark_safe(s)

    def make_active(self):
        active_req = self.__get_active()

        if active_req is not None:
            active_req.request = self
            active_req.save()
        else:
            active_req = ActiveRequest(course_offering = self.course_offering,
                                       user = self.student,
                                       request = self)
            active_req.save()

    def make_inactive(self):
        active_req = self.__get_active()

        if active_req is not None and active_req.request == self:
            active_req.delete()

    def cancel(self):
        self.state = Request.STATE_CANCELLED
        self.make_inactive()
        self.save()

    def schedule(self, slot, server):
        self.state = Request.STATE_SCHEDULED
        self.server = server
        self.actual_slot = slot
        self.save()

    def send_notification_email(self, template, cc_users=None, dry_run=False, update=False):
        t = get_template(template)
        body = t.render({"request": self})

        student = self.student

        if settings.DEBUG:
            recipient = settings.DEBUG_EMAIL
            if recipient is None:
                return False
        else:
            recipient = student.email

        recipient = '{} {} <{}>'.format(student.first_name, student.last_name, recipient)

        if cc_users is not None:
            cc = ['{} {} <{}>'.format(u.first_name, u.last_name, u.email) for u in cc_users if u != student]
        else:
            cc = []

        if update:
            subject = "An update on your {} office hours request".format(self.course_offering.catalog)
        else:
            subject = 'Your {} Office Hours Request'.format(self.course_offering.catalog)

        email = EmailMessage(
            subject,
            body,
            'CS 121 Office Hours <{}>'.format(settings.CONTACT_EMAIL),
            [recipient],
            cc=cc
        )

        email_success = True
        if dry_run:
            print(email)
        else:
            try:
                email.send()
            except SMTPException as e:
                print(e)
                email_success = False

        return email_success

    def start_service(self, server):
        self.state = Request.STATE_INPROGRESS
        self.server = server
        self.service_start_time = timezone.localtime(timezone.now())
        self.save()

    def complete_service(self):
        self.state = Request.STATE_COMPLETED
        self.make_inactive()
        self.service_end_time = timezone.localtime(timezone.now())
        self.save()

    def no_show(self):
        self.state = Request.STATE_NOSHOW
        self.make_inactive()
        self.save()

    def could_not_see(self):
        self.state = Request.STATE_COULDNOTSEE
        self.make_inactive()
        self.save()

    def __str__(self):
        return "{} -- {} -- {} ({})".format(self.student,
                                       self.course_offering.catalog_quarter,
                                       self.created_at,
                                       self.get_state_display())


class ActiveRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, null=False)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, null=False)

    class Meta:
        unique_together = (('user', 'course_offering'),)