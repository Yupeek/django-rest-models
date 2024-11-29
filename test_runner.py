# -*- coding: utf-8 -*-
import logging

from django.test.runner import DiscoverRunner

logger = logging.getLogger(__name__)


class NoCheckDiscoverRunner(DiscoverRunner):
    def run_checks(self, *args, **kwargs):
        pass
