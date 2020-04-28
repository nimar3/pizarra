FROM python:3.7-buster
COPY . /opt/pizarra
WORKDIR /opt/pizarra
RUN pip install -r requirements-pgsql.txt
ENV PYTHONPATH="$PYTHONPATH:/opt/pizarra"
CMD [ "/usr/local/bin/python3.7", "/opt/pizarra/worker.py"]