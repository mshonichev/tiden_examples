#!/usr/bin/env python3

from tiden.tidenplugin import TidenPlugin
from tiden.util import log_print
from tiden import TidenException

from os import system, getcwd, chdir, unlink, walk
from os.path import dirname, abspath, join, basename, getmtime
from datetime import datetime
from glob import glob

TIDEN_PLUGIN_VERSION = '1.0.0'


class MavenBuild(TidenPlugin):

    mvn_command = 'mvn'
    always_rebuild = False
    save_build_log = True

    def __init__(self, *args, **kwargs):
        TidenPlugin.__init__(self, *args, **kwargs)
        if 'mvn_cmd' in self.options:
            self.mvn_command = self.options['mvn_cmd']
        if 'save_build_log' in self.options:
            self.save_build_log = bool(self.options['save_build_log'])
        if 'always_rebuild' in self.options:
            self.always_rebuild = bool(self.options['always_rebuild'])
        self.build_log_name = ''

    def before_prepare_artifacts(self, *args, **kwargs):
        """
        Before prepare artifacts
        :param args:
                config
        """
        config = args[0]
        if 'artifacts' in config:
            for artifact_name, artifact in config['artifacts'].items():
                if 'mvn' in artifact:
                    if 'build_path' not in artifact['mvn']:
                        raise TidenException("mvn section of artifact must have 'build_path' attribute")
                    build_path = artifact['mvn']['build_path']
                    if self._need_rebuild(artifact, build_path):
                        mvn_args = artifact['mvn'].get('mvn_args', '')
                        if not self._build_maven_artifact(artifact_name, build_path, mvn_args):
                            build_log = basename(self._get_maven_build_log_name())
                            raise TidenException(f"Can't build maven artifact '{artifact_name}', "
                                                 f"inspect build log '{build_log}' in {build_path} for errors")
                        else:
                            if not self.save_build_log:
                                build_log = self._get_maven_build_log_name()
                                unlink(build_log)
                    del artifact['mvn']

    def _get_maven_build_log_name(self):
        return self.build_log_name

    def _build_maven_artifact(self, artifact_name, build_path, mvn_args):
        log_print(f"Building maven artifact '{artifact_name}' ...")
        build_path = abspath(build_path)
        current_directory = getcwd()
        timestamp = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
        self.build_log_name = join(build_path, f'maven-build-{timestamp}.log')
        chdir(build_path)
        try:
            rc = system(' '.join([self.mvn_command, mvn_args, f' > {self.build_log_name} 2>&1 ']))
        finally:
            chdir(current_directory)
        return rc == 0

    def _need_rebuild(self, artifact, build_path):
        if self.always_rebuild:
            return True
        if 'always_rebuild' in artifact['mvn'] and bool(artifact['mvn']['always_rebuild']):
            return True
        artifact_jar = glob(artifact['glob_path'])
        if not artifact_jar:
            return True

        files_stat = {}
        for root, dirs, files in walk(build_path):
            for file in files:
                files_stat[file] = getmtime(join(root, file))
