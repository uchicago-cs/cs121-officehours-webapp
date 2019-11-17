from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


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
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=64)

    def __str__(self):
        return "{} ({})".format(self.date, self.interval)

    @property
    def interval(self):
        start = self.start_time.strftime("%I:%M %p")
        end = self.end_time.strftime("%I:%M %p")
        return "{} - {}".format(start, end)


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
    additional_students = models.ManyToManyField(User, related_name="additional_requests")
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

    def get_state_class(self):
        if self.state in (Request.STATE_PENDING,):
            return "btn-warning"
        elif self.state in (Request.STATE_SCHEDULED, Request.STATE_INPROGRESS):
            return "btn-success"
        elif self.state in (Request.COMPLETED,):
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