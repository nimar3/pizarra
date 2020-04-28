FROM python:3.7-buster
COPY . /opt/pizarra
WORKDIR /opt/pizarra
RUN pip install -r requirements-pgsql.txt
ENV PYTHONPATH="$PYTHONPATH:/opt/pizarra"
EXPOSE 5005
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]