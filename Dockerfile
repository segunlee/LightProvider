FROM python:3
MAINTAINER LEE SEGUN <segunleedev@gmail.com>

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY lightcomics.json.default /usr/src/app/lightcomics.json
COPY lightcomics.py /usr/src/app

EXPOSE 8909

CMD ["python", "./lightcomics.py"]