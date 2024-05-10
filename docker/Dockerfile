# Dockerfile
FROM python:3.9-slim

# 環境変数を設定
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# アプリケーションのコードをコンテナにコピー
COPY .. /app/
