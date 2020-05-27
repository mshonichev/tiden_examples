# tiden_examples

Playground for Tiden Ignite examples before publication.

## Install pre-requisites

Install Tiden from Test PyPi:

```bash
    sudo -H pip3.7 install --index-url https://test.pypi.org/simple/ tiden
```

Alternatively, you can install Tiden from sources: 

```bash
    git clone git@github.com:mshonichev/tiden_pkg.git
    cd tiden_pkg
    bash ./build.sh
    bash ./install.sh
```

## Checkout examples
To clone this example git repository you must have Git Lfs installed.
https://git-lfs.github.com/

```bash
    git clone git@github.com:mshonichev/tiden_examples.git
    cd tiden_examples
```

## Run examples suite
Examples suite shows up simple test scenarios based on GeneralTestCase and AppTestCase.

```bash
    cd tiden_examples
    bash ./run_examples.sh
```

## Run gatling suite
Gatling suite uses custom application and plugin to build and run Gatling scenario against Ignite instance.

```bash
    cd tiden_examples
    bash ./run_gatling.sh
```
