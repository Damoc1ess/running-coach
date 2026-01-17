#!/bin/bash

# Demarrer l'API FastAPI en arriere-plan
echo "Demarrage de l'API FastAPI sur le port 8000..."
uvicorn api_endpoints:app --host 0.0.0.0 --port 8000 &

# Attendre que l'API soit prete
sleep 2

# Demarrer le dashboard Streamlit
echo "Demarrage du dashboard Streamlit sur le port 8501..."
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
