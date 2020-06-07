#!/bin/bash

environment=${USER}
if [ ! -f config/env_${environment}.yaml ]; then
  environment=default
fi

tiden run-tests \
    --ts=examples \
    --tc=config/env_${environment}.yaml \
    --tc=config/artifacts-ai.yaml \
    --clean=tests


