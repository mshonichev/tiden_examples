#!/usr/bin/env python3

from apps.gatling import Gatling
from tiden.apps.ignite import Ignite
from tiden.case.apptestcase import AppTestCase
from tiden.util import log_print

import time


class TestGatling (AppTestCase):

    def __init__(self, *args):
        super().__init__(*args)
        self.add_app('gatling')
        self.add_app('ignite')

    def setup(self):
        self.create_app_config_set(
            Ignite,
            addresses=self.get_ignite_hosts(),
            zookeeper_enabled=False,
        )
        super().setup()

    def get_ignite_hosts(self):
        if 'ignite' in self.tiden.config['environment']:
            return self.tiden.config['environment']['ignite'].get('server_hosts', [])
        else:
            return self.tiden.config['environment'].get('server_hosts', [])

    def test_run_gatling_test(self):
        """
        Start Ignite, put some load onto REST endpoint
        """
        gatling_app: Gatling = self.get_app('gatling')
        ignite_app: Ignite = self.get_app('ignite')
        ignite_app.set_node_option(
            '*', 'config', Ignite.config_builder.get_config('server')
        )
        ignite_app.start_nodes()

        rest_host = ignite_app.nodes[1]['host']
        rest_port = ignite_app.nodes[1]['rest_port']
        load_url = f"http://{rest_host}:{rest_port}/ignite?cmd=top"
        log_print(f"Starting HTTP Load -> {load_url}")
        gatling_app.start(
            scenario="perftest.HttpLoadScenario",
            args={
                "baseUrl": load_url,
                "duration": 60,
                "load_factor": 100,
                "load_throttle": 5,
            },
        )

        time.sleep(120)

