from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from tz.models import Course, Student, CourseParticipant


class CRUDCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

    def validate(self, attrs):
        if attrs.get('start_date') > attrs.get('end_date'):
            raise ValidationError('End date should be after start date')

        return attrs


class CourseListSerializer(serializers.ModelSerializer):
    class Meta(CRUDCourseSerializer.Meta):
        pass

    students_count = serializers.IntegerField()


class StudentAssignmentSerializer(serializers.Serializer):
    class Meta:
        fields = ('students',)

    course = serializers.SlugRelatedField(
        queryset=Course.objects.all(),
        slug_field='pk',
    )
    students = serializers.ListField(child=serializers.IntegerField())

    def validate(self, attrs):
        students_id = set(attrs.get('students'))
        if len(students_id) != Student.objects.filter(pk__in=students_id).count():
            raise ValidationError('Invalid student IDs')
        return attrs

    def create(self, validated_data):
        course = validated_data.get('course')
        participants = [
            CourseParticipant(course=course, student_id=student_id)
            for student_id in validated_data.get('students')
        ]

        # ignore_conflicts to ignore failure on unique constrain for already assigned students
        return CourseParticipant.objects.bulk_create(participants, ignore_conflicts=True)

    def destroy(self):
        course = self.validated_data.get('course')
        return CourseParticipant.objects.filter(
            course=course, student_id__in=self.validated_data.get('students')
        ).delete()
