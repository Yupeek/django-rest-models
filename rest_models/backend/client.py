import os
import subprocess

from django.db.backends.base.client import BaseDatabaseClient
from django.test.testcases import LiveServerThread, _StaticFilesHandler

from rest_models.backend.connexion import LocalApiAdapter


class DatabaseClient(BaseDatabaseClient):
    executable_name = 'bash'
    port_range = (8097, 9015)

    def start_server_thread(self):
        self.server_thread = LiveServerThread('localhost',
                                              _StaticFilesHandler)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Wait for the live server to be ready
        self.server_thread.is_ready.wait()
        if self.server_thread.error:
            # Clean up behind ourselves, since tearDownClass won't get called in
            # case of errors.
            self.stop_server_thread()
            raise self.server_thread.error
        return 'http://%s:%s' % (
                self.server_thread.host, self.server_thread.port)

    def stop_server_thread(self):
        # There may not be a 'server_thread' attribute if setUpClass() for some
        # reasons has raised an exception.
        if hasattr(self, 'server_thread'):
            # Terminate the live server's thread
            self.server_thread.terminate()
            self.server_thread.join()

    def runshell(self):
        resty_path = os.path.join(os.path.dirname(__file__), "exec", "resty")
        args = [self.executable_name, "--init-file", resty_path]

        cname = self.connection.settings_dict['NAME']
        if cname.startswith(LocalApiAdapter.SPECIAL_URL):
            cname = cname.replace(LocalApiAdapter.SPECIAL_URL, self.start_server_thread())
        cname = cname.rstrip("/") + "*"
        envs = os.environ.copy()
        envs.update(dict(
            _EXTRA_CURL_AUTH=self.get_middleware_curl_args(),
            _resty_host=cname)
        )
        self.execute_subprocess(args=args, env=envs)

        self.stop_server_thread()

    def execute_subprocess(self, args, env):
        subprocess.call(args, env=env)  # pragma: no cover

    def get_middleware_curl_args(self):
        """
        return the curl extra args to authorize ourselve to the api
        :return:
        """
        return ""
