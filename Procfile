# web: bin/web
web: gunicorn ironman:app
init: python db_create.py && pybabel compile -d CC2013/translations
upgrade: python db_upgrade.py && pybabel compile -d CC2013/translations
