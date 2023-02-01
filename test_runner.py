# -*- coding: utf-8 -*-
import logging

from django.test.runner import DiscoverRunner
from teamcity.django import TeamcityDjangoRunner

logger = logging.getLogger(__name__)


class NoCheckDiscoverRunner(DiscoverRunner):
    def run_checks(self, *args, **kwargs):
        pass


class NoCheckTeamcityDjangoRunner(TeamcityDjangoRunner):
    def run_checks(self, *args, **kwargs):
        pass
