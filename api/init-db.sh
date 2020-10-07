#!/usr/bin/bash

# DBファイルの削除
rm -rf ./api/migrations
rm -rf db.sqlite3

# マイグレーション
read -p "Please enter the app name:" app_name
python manage.py makemigrations $app_name

# マイグレート
python manage.py migrate

# デフォルトデータの作成
python manage.py loaddata fixture-week.json
python manage.py loaddata fixture-default-category.json

# スーパーユーザーの作成
python manage.py createsuperuser

# サーバー起動
python manage.py runserver 0.0.0.0:8000
