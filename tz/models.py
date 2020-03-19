from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=1024)
    start_date = models.DateField()
    end_date = models.DateField()


class Student(models.Model):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    email = models.EmailField()


class CourseParticipant(models.Model):
    class Meta:
        unique_together = (('course', 'student'),)

    course = models.ForeignKey('tz.Course', on_delete=models.CASCADE)
    student = models.ForeignKey('tz.Student', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
