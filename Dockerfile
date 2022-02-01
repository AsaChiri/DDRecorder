FROM python:3.10
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-u", "main.py", "config/config.json"]
