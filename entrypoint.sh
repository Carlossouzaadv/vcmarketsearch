#!/bin/bash
set -e

# Use PORT environment variable from Railway, default to 8501
PORT=${PORT:-8501}

# Start Streamlit with the correct port
exec streamlit run streamlit_app.py \
  --server.port=$PORT \
  --server.address=0.0.0.0 \
  --server.headless=true
