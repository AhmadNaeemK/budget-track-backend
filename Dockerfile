FROM python:3
COPY Pipfile /
COPY Pipfile.lock /
COPY budget-tracker/ /
RUN pip install pipenv
RUN pipenv install --system
EXPOSE 8000

ENTRYPOINT ["python"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]