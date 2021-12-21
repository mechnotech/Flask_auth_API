FROM python:3.10.0-slim-buster
LABEL name='Auth API' version=1
RUN apt-get update && apt-get install -y iputils-ping
WORKDIR /code
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
COPY ./ /code
CMD ["python3", "/code/main.py"]