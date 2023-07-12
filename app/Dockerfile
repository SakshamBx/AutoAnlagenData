FROM python:3.12.0b3-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_APP=main.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001", "--reload"]
