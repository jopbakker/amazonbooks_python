FROM python:3-alpine

WORKDIR /app

RUN apk add gcc g++ make libffi-dev openssl-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY amazonbooks.py .

ENTRYPOINT ["python", "amazonbooks.py"]
#ENTRYPOINT ["python"]