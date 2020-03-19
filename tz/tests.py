import io
from datetime import timedelta

import pandas as pd
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from tz.models import Course, Student, CourseParticipant


class TZTests(APITestCase):
    def test_CRUD_course(self):
        list_url = reverse('courses-list')

        start_date = timezone.now()
        data = {
            'name': 'Black Magic',
            'description': 'Crucio',
            'start_date': start_date.date(),
            'end_date': (start_date + timedelta(days=1)).date()
        }

        response = self.client.post(list_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)

        detail_url = reverse('courses-detail', kwargs={'pk': Course.objects.first().pk})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), Course.objects.first().name)

        new_name = 'White Magic'
        data['name'] = new_name
        response = self.client.put(detail_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), new_name)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 0)

        # date validation
        data['end_date'] = (start_date - timedelta(days=1)).date()
        response = self.client.post(list_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Course.objects.count(), 0)

    def create_init_data(self):
        courses = [
            Course(
                name=f'name_{i}',
                description=f'desc_{i}',
                start_date=timezone.now().date(),
                end_date=(timezone.now() + timedelta(days=1)).date()
            ) for i in range(2)
        ]
        Course.objects.bulk_create(courses)

        students = [
            Student(
                first_name=f'test_{i}',
                last_name=f'test_{i}',
                email=f'test_{i}@test.com'
            ) for i in range(3)]
        Student.objects.bulk_create(students)

    def test_list_API_course(self):
        self.create_init_data()

        course = Course.objects.first()
        url = reverse('courses-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual([c.get('students_count') for c in response.data], [0, 0])

        CourseParticipant.objects.bulk_create(
            CourseParticipant(course=course, student=student) for student in Student.objects.all()
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual([c.get('students_count') for c in response.data], [3, 0])

    def test_assign_unassign_API(self):
        self.create_init_data()
        assign_url = reverse('assignment-assign')
        unassign_url = reverse('assignment-unassign')

        course = Course.objects.first()
        response = self.client.post(
            assign_url, {'course': course.pk, 'students': [Student.objects.last().pk + 1]}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CourseParticipant.objects.count(), 0)

        response = self.client.post(
            assign_url,
            {'course': course.pk, 'students': Student.objects.values_list('pk', flat=True)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            CourseParticipant.objects.filter(course=course).count(),
            Student.objects.count()
        )

        student = Student.objects.first()
        response = self.client.post(unassign_url, {'course': course.pk, 'students': [student.pk]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            CourseParticipant.objects.filter(course=course, student=student).count(), 0
        )
        self.assertEqual(CourseParticipant.objects.count(), 2)


    def test_get_csv_report(self):
        self.create_init_data()
        url = reverse('report-list')
        students = Student.objects.all()[:2]
        participants = [
            CourseParticipant(student=students[0], course=c) for c in Course.objects.all()
        ]
        participants.extend([
            CourseParticipant(
                student=students[1], course=c, completed=True
            ) for c in Course.objects.all()
        ])
        CourseParticipant.objects.bulk_create(participants)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(content))
        self.assertEqual(
            sorted(row.to_dict().get('courses') for _, row in df.iterrows()),
            [0, 2, 2]
        )
        self.assertEqual(
            sorted(row.to_dict().get('completed_courses') for _, row in df.iterrows()),
            [0, 0, 2]
        )
