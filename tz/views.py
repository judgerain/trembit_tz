from django.db.models import Count, Value as V, Q
from django.db.models.functions import Concat
from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from tz.models import Course, Student
from tz.report_utils import ReportCreator
from tz.serializers import CRUDCourseSerializer, CourseListSerializer, StudentAssignmentSerializer


class CRUDCourseViewSet(viewsets.ModelViewSet):
    serializer_class = CRUDCourseSerializer
    queryset = Course.objects.all()

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()
        if self.action == 'list':
            serializer_class = CourseListSerializer
        return serializer_class

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.annotate(students_count=Count('courseparticipant__student'))
        return queryset


class AssignViewSet(viewsets.GenericViewSet):
    serializer_class = StudentAssignmentSerializer

    @action(detail=False, methods=['POST'])
    def assign(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('Assigned')

    @action(detail=False, methods=['POST'])
    def unassign(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.destroy()
        return Response('Unassigned')


class ReportViewSet(viewsets.GenericViewSet):
    def list(self, request):
        data = Student.objects.annotate(
            full_name=Concat('first_name', V(' '), 'last_name'),
            courses=Count('courseparticipant__course'),
            completed_courses=Count(
                'courseparticipant__course',
                filter=Q(courseparticipant__completed=True)
            )
        ).values('full_name', 'courses', 'completed_courses')

        file = ReportCreator(data).create_csv()

        return HttpResponse(file, content_type='text/csv')
