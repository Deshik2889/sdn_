#!/bin/bash

echo "🛑 Stopping SDN system..."

sudo mn -c
docker stop onos

pkill -f congestion_detection.py
pkill -f ewma_prediction.py
pkill -f reroute.py
pkill -f backend.py

echo "✅ System stopped cleanly"
