FROM python:3.11-slim

WORKDIR /app

# Korean font for matplotlib charts
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-nanum \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clear matplotlib font cache so it picks up NanumGothic
RUN python -c "import matplotlib; matplotlib.font_manager._load_fontmanager(try_read_cache=False)"

COPY . .

RUN mkdir -p output/latest output/history

EXPOSE 8501

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

CMD ["streamlit", "run", "dashboard/app.py"]
