# syntax=docker/dockerfile:1
FROM python:3.9-alpine

RUN apk add --no-cache gcc musl-dev linux-headers
RUN apk update \
    && apk add bash \
    && apk add curl zip git unzip iputils

# install aws cli
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install -i /usr/local/aws-cli -b /usr/local/bin \
    && rm awscliv2.zip

WORKDIR /code
ENV FLASK_APP=application.py
ENV FLASK_RUN_HOST=0.0.0.0

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 5000
COPY . .

CMD ["flask", "run"]