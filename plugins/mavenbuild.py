#!/usr/bin/env python3
#
# Copyright 2017-2020 GridGain Systems.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tiden.tidenplugin import TidenPlugin
from tiden.util import log_print
from tiden import TidenException

from os import system, getcwd, chdir, unlink, walk
from os.path import dirname, abspath, join, basename, getmtime
from datetime import datetime
from glob import glob
from re import match

TIDEN_PLUGIN_VERSION = '1.0.0'


class MavenBuild(TidenPlugin):
    # pattern of file names ignored when detecting source changes
    ignore_files = r'^(\.git.*|.*\.log)$'

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
                    if self._need_rebuild(
                            artifact,
                            build_path,
                            artifact['mvn'].get('ignore_files', MavenBuild.ignore_files)
                    ):
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

    def _need_rebuild(self, artifact, build_path, ignore_files):
        if self.always_rebuild:
            return True
        if 'always_rebuild' in artifact['mvn'] and bool(artifact['mvn']['always_rebuild']):
            return True
        artifact_jars = glob(artifact['glob_path'])
        if not artifact_jars:
            return True

        max_jar_mtime = 0
        for artifact_jar in artifact_jars:
            cur_jar_mtime = getmtime(artifact_jar)
            if cur_jar_mtime > max_jar_mtime:
                max_jar_mtime = cur_jar_mtime

        max_mtime = 0
        for root, dirs, files in walk(build_path):
            if root != build_path:
                if root.startswith(join(build_path, 'target')):
                    continue

            for file in files:
                if match(ignore_files, file):
                    continue
                cur_mtime = getmtime(join(root, file))
                if cur_mtime > max_mtime:
                    max_mtime = cur_mtime
                    if max_mtime > max_jar_mtime:
                        return True

        return False

