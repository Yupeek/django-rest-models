# -*- coding: utf-8 -*-
import logging
import os
from uuid import uuid4

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from testapi import models as apimodels
from testapp import models as clientmodels

logger = logging.getLogger(__name__)

white_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$' \
            b'\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00 cHRM\x00\x00z&' \
            b'\x00\x00\x80\x84\x00\x00\xfa\x00\x00\x00\x80\xe8\x00\x00u0\x00\x00\xea`\x00\x00:' \
            b'\x98\x00\x00\x17p\x9c\xbaQ<\x00\x00\x00\x02bKGD\x00\x01\xdd\x8a\x13\xa4\x00\x00\x00\x07tIME' \
            b'\x07\xe2\n\x1e\x0f2\nk\xd7\xd2v\x00\x00\x00\nIDAT\x08\xd7ch\x00\x00\x00\x82\x00\x81\xddCj' \
            b'\xf4\x00\x00\x00%tEXtdate:create\x002018-10-30T15:50:10+01:00p\xa6\x80\xd1\x00\x00\x00%t' \
            b'EXtdate:modify\x002018-10-30T15:50:10+01:00\x01\xfb8m\x00\x00\x00\x00IEND\xaeB`\x82'


class TestUploadDRF(TestCase):
    fixtures = ['user.json']

    def setUp(self):
        self.img_name = str(uuid4()) + '.png'
        self.unlinkimg(self.img_name)

    def tearDown(self):
        self.unlinkimg(self.img_name)

    def unlinkimg(self, img_name):
        path = os.path.join(settings.MEDIA_ROOT, img_name)
        if os.path.exists(path):
            os.unlink(path)

    def test_url_files(self):

        review_api = apimodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, white_png, 'image/png'),
        )
        self.assertEqual(review_api.photo.name, self.img_name)
        self.assertEqual(review_api.photo.url, '/media/%s' % self.img_name)
        review_api.refresh_from_db()
        self.assertEqual(review_api.photo.name, self.img_name)
        self.assertEqual(review_api.photo.url, '/media/%s' % self.img_name)

        review_client = clientmodels.Review.objects.get(pk=review_api.pk)
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)

        self.assertEqual(review_client.photo.name, self.img_name)

    def test_upload_files(self):

        review_client = clientmodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, white_png, 'image/png'),
        )

        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        self.assertEqual(review_client.photo.name, self.img_name)
        review_client.refresh_from_db()
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        self.assertEqual(review_client.photo.name, self.img_name)

        review_api = clientmodels.Review.objects.get(pk=review_client.pk)
        self.assertEqual(review_api.photo.name, self.img_name)
        self.assertEqual(review_api.photo.url, 'http://testserver/media/%s' % self.img_name)

    def test_open_from_api(self):
        review_api = apimodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, white_png, 'image/png'),
        )
        self.assertEqual(review_api.photo.file.read(), white_png)
        review_api.refresh_from_db()
        self.assertEqual(review_api.photo.file.read(), white_png)

        review_client = clientmodels.Review.objects.get(pk=review_api.pk)
        self.assertEqual(review_client.photo.url, 'http://testserver/media/%s' % self.img_name)
        self.assertEqual(review_client.photo.file.read(), white_png)

    def test_open_from_client(self):
        review_client = apimodels.Review.objects.create(
            comment="coucou",
            photo=SimpleUploadedFile(self.img_name, white_png, 'image/png'),
        )
        self.assertEqual(review_client.photo.file.read(), white_png)
        review_client.refresh_from_db()
        self.assertEqual(review_client.photo.file.read(), white_png)

        review_api = apimodels.Review.objects.get(pk=review_client.pk)
        self.assertEqual(review_api.photo.file.read(), white_png)
