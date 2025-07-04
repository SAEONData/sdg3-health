FROM python:3.12-slim-bullseye

WORKDIR /app

ENV HOME=/app

RUN apt-get update --fix-missing && \ 
    apt-get install -y --no-install-recommends \ 
    build-essential libpq-dev && \
    apt-get autoclean && \
    apt-get autoremove && \ 
    rm -rf /var/lib/{apt,dpkg,cache,log,lists}

RUN addgroup --system sdg3grp && adduser --system --ingroup sdg3grp sdg3usr 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R sdg3usr:sdg3grp /app

USER sdg3usr

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=false", \
    "--server.baseUrlPath=sdg3health"]
    