# Twilio Monitor

[![Docker](https://img.shields.io/badge/Docker-24.0.5-1488C6.svg?logo=docker&style=plastic)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11.0-3776AB.svg?logo=python&style=plastic)](https://www.python.org/)
[![Twilio](https://img.shields.io/badge/-Twilio-F22F46.svg?logo=twilio&style=plastic)](https://www.twilio.com/en-us)
[![Sentry](https://img.shields.io/badge/-Sentry-FB4226.svg?logo=sentry&style=plastic)](https://sentry.io/welcome/)
[![Deploy](https://github.com/crab85193/twilio-monitor/actions/workflows/deploy.yml/badge.svg)](https://github.com/crab85193/twilio-monitor/actions/workflows/deploy.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

![logo](./docs/img/logo-w.png)

[English README is here](./README.md)

## Description
代理電話予約サービス[Tely](https://github.com/crab85193/Tely)で使用する通話状態監視プログラム。
Twilioから取得した通話状態をもとに、データベースに最新の通話状態を記録する。

## Requirement
- Ubuntu22.04
- Docker 24.0.5
- Python 3.11.0
- Sentry-sdk 1.39.1
- twilio 8.11.0

## Usage
このプログラムを実行するためには、Dockerのインストールと、[Tely](https://github.com/crab85193/Tely)を起動させる必要があります。

`.env.dev`を作成し、以下の内容を記述します。

```
MYSQL_ROOT_PASSWORD={ROOT PASSWORD}
MYSQL_DATABASE={DATABASE NAME}
MYSQL_USER={USER NAME}
MYSQL_PASSWORD={USER PASSWORD}
MYSQL_HOST={HOST}
MYSQL_PORT={PORT}

SENTRY_DNS={SENTRY DNS ADDRESS}

TWILIO_ACCOUNT_SID={TWILIO ACCOUNT SID}
TWILIO_AUTH_TOKEN={TWILIO AUTH TOKEN}

```

`.env.dev` 作成後、以下のコマンドを実行し、コンテナを起動します。

```
$ docker-compose -f docker-compose.dev.yml up -d --build
```

## Reference

- [Python Documents](https://docs.python.org/3.11/)
- [Twilio Documents](https://www.twilio.com/docs)
- [Docker Documents](https://docs.docker.com/)

## License
Copyright © 2024 Team Quartetto Inc.

This software is released under the Apache 2.0 License, see [LICENSE](./LICENSE).
