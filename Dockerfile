FROM python:3.8


RUN apt-get update && apt-get install -y libpcre3 libpcre3-dev gcc wget libbluetooth-dev libcap2-bin bluetooth bluez blueman
# RUN setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
RUN useradd -ms /bin/bash uwsgi
RUN mkdir /app

ADD requirements.txt /app
WORKDIR /app

ENV PYTHONPATH $PYTHONPATH:/app

RUN pip install -r requirements.txt

ADD . /app
# RUN chmod 777 .tmp

STOPSIGNAL SIGHUP

CMD su uwsgi -c 'uwsgi uwsgi.ini --thunder-lock'