import os
import subprocess

from django.db.backends.base.client import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):
    executable_name = 'bash'

    def runshell(self):
        resty_path = os.path.join(os.path.dirname(__file__), "exec", "resty")
        args = [self.executable_name, "--init-file", resty_path]

        subprocess.call(args, env={
            "_EXTRA_CURL_AUTH": self.get_middleware_curl_args(),
            "_resty_host": self.connection.settings_dict['NAME'],

        })

    def get_middleware_curl_args(self):
        """
        return the curl extra args to authorize ourselve to the api
        :return:
        """
        return ""
