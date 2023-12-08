FROM python:3.12.0

ENV APP_HOME /app

WORKDIR ${APP_HOME}

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]  
