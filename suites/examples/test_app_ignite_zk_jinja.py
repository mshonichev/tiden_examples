#!/usr/bin/env python3

from time import sleep
from tiden.apps.ignite import Ignite
from tiden.case.apptestcase import AppTestCase
from tiden.util import log_print, require, attr


class TestAppIgniteZkJinja(AppTestCase):

    def __init__(self, *args):
        super().__init__(*args)
        self.add_app('ignite')
        self.add_app('zookeeper')

    def setup(self):
        self.create_app_config_set(Ignite, 'zoo', zookeeper_enabled=True)
        self.create_app_config_set(Ignite, 'tcp', zookeeper_enabled=False)
        super().setup()

    @attr('current')
    def run_ignite_grid(self):
        ignite_app = Ignite(self.get_app_by_type('ignite')[0])
        artifact_cfg = self.tiden.config['artifacts'][ignite_app.name]
        ignite_app.reset()
        log_print("Ignite ver. %s, revision %s" % (
            artifact_cfg['ignite_version'],
            artifact_cfg['ignite_revision'],
        ))
        ignite_app.start_nodes()
        ignite_app.cu.activate()
        sleep(10)
        ignite_app.cu.deactivate()
        ignite_app.stop_nodes()

    def test_start_grid_with_zk(self):
        Ignite.config_builder.current_config_set = 'zoo'
        ignite_app = self.get_app_by_type('ignite')[0]
        zk_app = self.get_app_by_type('zookeeper')[0]
        ignite_app.set_node_option(
            '*', 'jvm_options', ["-DZK_CONNECTION=%s" % zk_app._get_zkConnectionString()]
        )
        ignite_app.set_node_option(
            '*', 'config', Ignite.config_builder.get_config('server')
        )
        zk_app.start()
        self.run_ignite_grid()
        zk_app.stop()

    def test_start_grid(self):
        Ignite.config_builder.current_config_set = 'tcp'
        print(str(self.tiden.apps))
        ignite_app = self.get_app_by_type('ignite')[0]
        ignite_app.set_node_option('*', 'config', Ignite.config_builder.get_config('server'))
        self.run_ignite_grid()

    @require(min_server_nodes=2)
    def test_start_grid_exclusive_config(self):
        # set current context
        Ignite.config_builder.current_config_set = 'tcp'
        print(str(self.tiden.apps))

        # set config per all nodes
        ignite_app = self.get_app_by_type('ignite')[0]
        ignite_app.set_node_option(
            '*', 'config', Ignite.config_builder.get_config('server')
        )

        print("Add exclusive config for node 2 for all configuration sets")
        Ignite.config_builder.add_template_variables(
            config_set_name='*',
            node_id=2,
            consistent_id=ignite_app.nodes[2]['template_variables']['consistent_id']
        )
        Ignite.config_builder.build_config_and_deploy(config_type='server', node_id=2)
        ignite_app.set_node_option(2, 'config', Ignite.config_builder.get_config('server', node_id=2))

        print(Ignite.config_builder)

        # Add exclusive config for node 2 for all contexts
        #
        # Application config for app Ignite:
        #
        #   Current config set: tcp
        #
        #   Original configs: {'server': 'server.tmpl.xml', 'client': 'client.tmpl.xml'}
        #
        #   Config set: zoo
        #     Common template variables: {'zookeeper_enabled': True}
        #     Exclusive template variables: {2: {'consistent_id': 'node2'}}
        #     Common generated configs: {'server': 'server_zoo.xml', 'client': 'client_zoo.xml'}
        #     Exclusive generated configs: {2: {'server': 'server_zoo_2.xml'}}
        #
        #   Config set: tcp
        #     Common template variables: {'zookeeper_enabled': False}
        #     Exclusive template variables: {2: {'consistent_id': 'node2'}}
        #     Common generated configs: {'server': 'server_tcp.xml', 'client': 'client_tcp.xml'}
        #     Exclusive generated configs: {2: {'server': 'server_tcp_2.xml'}}

        print("Add exclusive config for node 1 for 'zoo' context only")
        Ignite.config_builder.add_template_variables(
            'zoo',
            node_id=1,
            consistent_id=ignite_app.nodes[1]['template_variables']['consistent_id']
        )

        # rebuild and redeploy exclusive config
        Ignite.config_builder.build_config_and_deploy(config_type='server', config_set_name='zoo', node_id=1)

        # ask Ignite application to use exclusive config for that node
        ignite_app.set_node_option(1, 'config', Ignite.config_builder.get_config(
            config_type='server',
            config_set_name='zoo',
            node_id=1
        ))

        print(Ignite.config_builder)

        # Add exclusive config for node 1 for 'zoo' context only
        #
        # Application config for app Ignite:
        #
        #   Current config set: tcp
        #
        #   Original configs: {'server': 'server.tmpl.xml', 'client': 'client.tmpl.xml'}
        #
        #   Config set: zoo
        #     Common template variables: {'zookeeper_enabled': True}
        #     Exclusive template variables: {2: {'consistent_id': 'node2'}, 1: {'consistent_id': 'node1'}}
        #     Common generated configs: {'server': 'server_zoo.xml', 'client': 'client_zoo.xml'}
        #     Exclusive generated configs: {2: {'server': 'server_zoo_2.xml'}, 1: {'server': 'server_zoo_1.xml'}}
        #
        #   Config set: tcp
        #     Common template variables: {'zookeeper_enabled': False}
        #     Exclusive template variables: {2: {'consistent_id': 'node2'}}
        #     Common generated configs: {'server': 'server_tcp.xml', 'client': 'client_tcp.xml'}
        #     Exclusive generated configs: {2: {'server': 'server_tcp_2.xml'}}

        print("Add exclusive config for node 1 for current = tcp context only")
        Ignite.config_builder.add_template_variables(
            node_id=1,
            consistent_id=ignite_app.nodes[1]['template_variables']['consistent_id']
        )
        Ignite.config_builder.build_config_and_deploy(config_type='server', node_id=1)
        ignite_app.set_node_option(1, 'config', Ignite.config_builder.get_config('server', node_id=1))

        print(Ignite.config_builder)

        # Add exclusive config for node 1 for default = tcp context only
        #
        # Application config for app Ignite:
        #
        #   Current config set: tcp
        #
        #   Original configs: {'server': 'server.tmpl.xml', 'client': 'client.tmpl.xml'}
        #
        #   Config set: zoo
        #     Common template variables: {'zookeeper_enabled': True}
        #     Exclusive template variables: {2: {'consistent_id': 'node2'}, 1: {'consistent_id': 'node1'}}
        #     Common generated configs: {'server': 'server_zoo.xml', 'client': 'client_zoo.xml'}
        #     Exclusive generated configs: {2: {'server': 'server_zoo_2.xml'}, 1: {'server': 'server_zoo_1.xml'}}
        #
        #   Config set: tcp
        #     Common template variables: {'zookeeper_enabled': False}
        #     Exclusive template variables: {2: {'consistent_id': 'node2'}, 1: {'consistent_id': 'node1'}}
        #     Common generated configs: {'server': 'server_tcp.xml', 'client': 'client_tcp.xml'}
        #     Exclusive generated configs: {2: {'server': 'server_tcp_2.xml'}, 1: {'server': 'server_tcp_1.xml'}}

        print("Cleanup exclusive configs")

        Ignite.config_builder.cleanup_exclusive_configs()

        print(Ignite.config_builder)

        # Cleanup exclusive configs
        #
        # Application config for app Ignite:
        #
        #   Current config set: tcp
        #
        #   Original configs: {'server': 'server.tmpl.xml', 'client': 'client.tmpl.xml'}
        #
        #   Config set: zoo
        #     Common template variables: {'zookeeper_enabled': True}
        #     Exclusive template variables: {}
        #     Common generated configs: {'server': 'server_zoo.xml', 'client': 'client_zoo.xml'}
        #     Exclusive generated configs: {}
        #
        #   Config set: tcp
        #     Common template variables: {'zookeeper_enabled': False}
        #     Exclusive template variables: {}
        #     Common generated configs: {'server': 'server_tcp.xml', 'client': 'client_tcp.xml'}
        #     Exclusive generated configs: {}

        # run ignite
        self.run_ignite_grid()

    def test_create_config_on_fly(self):
        # Create config set inside test

        # 1. Register config with disabled caches
        self.create_app_config_set(Ignite, 'tcp-disabled-caches', deploy=True, disabled_cache_configs=True)

        # 4. Set new config as default
        Ignite.config_builder.current_config_set = 'tcp-disabled-caches'
        print(Ignite.config_builder)

        # Setup server nodes config
        ignite_app = self.get_app_by_type('ignite')[0]
        ignite_app.set_node_option(
            '*', 'config', Ignite.config_builder.get_config('server')
        )

        # Run grid
        artifact_cfg = self.tiden.config['artifacts'][ignite_app.name]
        ignite_app.reset()
        log_print("Ignite ver. %s, revision %s" % (
            artifact_cfg['ignite_version'],
            artifact_cfg['ignite_revision'],
        ))
        ignite_app.start_nodes()
        ignite_app.cu.activate()
        sleep(10)

        # Verify that there is no caches in cluster
        assert len(ignite_app.get_cache_names()) == 0, "There is some caches on cluster"

        sleep(10)

        ignite_app.cu.deactivate()
        ignite_app.stop_nodes()

        self.remove_app_config_set(Ignite, 'tcp-disabled-caches')

    def teardown(self):
        super().teardown()
