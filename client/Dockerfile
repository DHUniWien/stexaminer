FROM python:3.10
WORKDIR /src/app
RUN mkdir received
RUN apt-get update && apt-get -y install vim tree
COPY requirements.txt .
COPY references .
RUN pip install -r requirements.txt
ENV FLASK_RUN_PORT 8001
EXPOSE 8001
CMD ["flask", "run", "--host=0.0.0.0",  "--port=8001"]
