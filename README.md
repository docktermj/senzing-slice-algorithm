# senzing-slice-algorithm

## Overview

1. [Evaluating Entity Resolution Results](https://pdfs.semanticscholar.org/ee8e/13f3f17a2660331a3a17ba8a7cfb06f9b61d.pdf)

## Clone repository

1. Set these environment variable values:

    ```console
    export GIT_ACCOUNT=docktermj
    export GIT_REPOSITORY=senzing-slice-algorithm
    ```

1. Follow steps in [clone-repository](https://github.com/docktermj/KnowledgeBase/blob/master/HowTo/clone-repository.md) to install the Git repository.

1. After the repository has been cloned, be sure the following are set:

    ```console
    export GIT_ACCOUNT_DIR=~/${GIT_ACCOUNT}.git
    export GIT_REPOSITORY_DIR="${GIT_ACCOUNT_DIR}/${GIT_REPOSITORY}"
    ```

## Run

1. Example:

    ```console
    cd ${GIT_REPOSITORY_DIR}

    python slice-algorithm.py test \
      --prior-csv-file tests/test-1/Gold.csv \
      --current-csv-file tests/test-1/r3.csv
    ```
