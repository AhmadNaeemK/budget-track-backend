FROM python:3
COPY Pipfile /
RUN pip install pipenv
RUN pipenv install
COPY budget-tracker/ /
EXPOSE 8000
CMD pipenv run python manage.py runserver
