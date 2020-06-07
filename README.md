# tiden_examples

Playground for Tiden Ignite examples before publication.

## Install pre-requisites

Install Tiden from Test PyPi:

```bash
    sudo -H pip3.7 install --index-url https://test.pypi.org/simple/ tiden
```

Alternatively, you can install Tiden from sources: 

```bash
    git clone git@github.com:gridgain/tiden.git
    cd tiden
    bash ./build.sh
    bash ./install.sh
```

## Checkout examples
To clone this example git repository you must have Git Lfs installed.
https://git-lfs.github.com/

```bash
    git clone git@github.com:gridgain/tiden_examples.git
    cd tiden_examples
```

## Running test suites

### Provision hosts for running the test
Use your favourite means to provision some hosts for running the test - bare metal, AWS, docker.

Create `config/env_${USER}.yaml` file and put provisioned hosts into it. Unless `config/env_${USER}.yaml` exists, 
`config/env_default.yaml` will be used. Tune `servers_per_host` and `clients_per_host` according to your means. 

```yaml
environment:
    server_hosts:
      - <IP address 1>
      ...
      - <IP address N>
    servers_per_host: 1
    client_hosts:
      - <IP address 1>
      ...
      - <IP address N>
    clients_per_host: 1
```

Hosts should be accessible via SSH private key. You should put remote name and path to your environment config. 

```yaml
environment:
    username: ${USER}
    private_key_path: ${HOME}/.ssh/id_rsa
```

Create remote folder at the same location at all hosts, for example: `/home/${USER}/tests`.

```yaml
environment:
    ...
    home: /home/${USER}/tests
```

Install your favourite JDK at all hosts at the same location, for example `/usr/local/lib/java-8-oracle`. 

Remote JAVA_HOME can be set in the environment config as follows:

```yaml
environment:
    ...
    env_vars: 
        JAVA_HOME: /usr/local/lib/java-8-oracle
        PATH: $JAVA_HOME/bin:$PATH
```


### Run examples suite

Examples suite shows up simple test scenarios based on GeneralTestCase and AppTestCase.

```bash
    bash ./run_examples.sh
```

## Run gatling suite
Gatling suite uses custom application and plugin to build and run Gatling scenario against Ignite instance REST API.

```bash
    bash ./run_gatling.sh
```
