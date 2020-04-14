FROM python:3
MAINTAINER Jonghak Choi <haginara@gmail.com>

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY lightcomics.json.default /usr/src/app/lightcomics.json
COPY lightcomics.py /usr/src/app

EXPOSE 31258

CMD ["python", "./lightcomics.py"]