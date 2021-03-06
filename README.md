# erc20-bridge-serverless
[![CircleCI](https://circleci.com/gh/AlisProject/erc20-bridge-serverless/tree/master.svg?style=svg)](https://circleci.com/gh/AlisProject/erc20-bridge-serverless/tree/master)

# Prerequisite
- node.js
- yarn
- Python3
- Docker

# Install & Setup

```bash
git clone git@github.com:AlisProject/erc20-bridge-serverless.git
cd erc20-bridge-serverless

# yarn
yarn

# venv
python -m venv venv
source venv/bin/activate

# pip
pip install -r requirements.txt

# envrc
cp .envrc.sample .envrc
vi .envrc
direnv allow
```

# Test
## Setup DynamoDB Local
Download and unzip the [dynamoDB local zip](https://docs.aws.amazon.com/ja_jp/amazondynamodb/latest/developerguide/DynamoDBLocal.html) in any directory

For example
```
$ curl -O https://s3-ap-northeast-1.amazonaws.com/dynamodb-local-tokyo/dynamodb_local_latest.tar.gz
$ tar xf ./dynamodb_local_latest.tar.gz
$ rm ./dynamodb_local_latest.tar.gz
```

## Execute Test

```bash
# Start dynamoDB local
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

# exec
yarn test
```

# Register SSM Parameters

```bash
# Set environment variable of operator's private key in public chain.
export OPERATOR_PUBLIC_CHAIN_PRIVATE_KEY=0x...

# Set environment variable of operator's private key in private chain.
export OPERATOR_PRIVATE_CHAIN_PRIVATE_KEY=0x...

script/register_ssm_parameters.sh
```

# Deployment
** Docker is required to deploy **

```bash
yarn deploy
```

# Deletion

```bash
yarn destroy
```
