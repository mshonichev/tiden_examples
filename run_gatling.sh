#!/bin/bash

tiden run-tests \
    --ts=gatling \
    --tc=config/env_mshonichev.yaml \
    --tc=config/plugins-maven.yaml \
    --tc=config/artifacts-ai.yaml \
    --tc=config/artifacts-gatling.yaml \
    --tc=config/artifacts-flamegraph.yaml \
    --clean=tests

