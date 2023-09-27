FROM python:3.9.17-slim
WORKDIR /usr/src/app
COPY app.py .
COPY requirements.txt .
COPY .env .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
CMD [ "python", "./app.py"]
