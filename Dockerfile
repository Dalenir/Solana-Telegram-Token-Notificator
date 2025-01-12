FROM python:3.13-slim-bookworm

RUN apt update -y
RUN apt install -y build-essential

RUN pip install --upgrade pip
RUN pip install uv
ENV VIRTUAL_ENV /usr/local/

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN uv pip install --system -r requirements.txt

COPY ./src .

CMD ["python", "app.py"]

