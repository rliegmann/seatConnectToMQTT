# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim as base

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN  pip3 install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser


############################  STRAT as DEBUGGER  ################################
FROM base as debug
RUN python -m pip install debugpy

#CMD ["python", '-m', "ptvsd", "--host", "0.0.0.0", "--port", "5678", "--wait", "/app/app.py"]
CMD ["python", "./app.py"] 

############################  STRAT as DEBUGGER  ################################
FROM base as prod
CMD ["python", "app.py"]
 