FROM ubuntu:bionic
MAINTAINER SYSNET-CZ "info@sysnet.cz"

RUN apt-get update \
    && apt-get -y install cron
RUN apt-get update \
    && apt-get install -y python3-pip python3.6-dev \
    && cd /usr/local/bin \
    && ln -s /usr/bin/python3.6 python \
    && pip3 install --upgrade pip

COPY pumpa-cron /etc/cron.d/pumpa-cron
RUN chmod 0644 /etc/cron.d/pumpa-cron
RUN crontab /etc/cron.d/pumpa-cron
RUN touch /var/log/cron.log

WORKDIR /opt/pumpa
COPY logs .
COPY data .
COPY megapumpa.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN chmod a+x megapumpa.py  && ln -s megapumpa.py  megapumpa

CMD cron && tail -f /var/log/cron.log

