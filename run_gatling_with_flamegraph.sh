#!/bin/bash

environment=${USER}
if [ ! -f config/env_${environment}.yaml ]; then
  environment=default
fi

tiden run-tests \
    --ts=gatling \
    --tc=config/env_${environment}.yaml \
    --tc=config/plugins-maven.yaml \
    --tc=config/artifacts-ai.yaml \
    --tc=config/artifacts-gatling.yaml \
    --tc=config/artifacts-flamegraph.yaml \
    --clean=tests

