#!/bin/bash
set -e

echo "⚡ Starting SDN Predictive Congestion Control System..."

# ==============================
# GLOBALS
# ==============================
BASE_DIR=$(pwd)
LOG_DIR="$BASE_DIR/logs"

ONOS_IMAGE="onosproject/onos"
ONOS_CONTAINER="onos"

CONTROLLER_IP="127.0.0.1"
OF_PORT="6653"

# ==============================
# PREP
# ==============================
echo "🧹 Preparing environment..."
mkdir -p "$LOG_DIR"
sudo mn -c > /dev/null 2>&1 || true

# Choose topology based on available memory (safer defaults for low-RAM hosts)
TOTAL_MEM_MB=$(free -m | awk '/Mem:/ {print $2}')
TOPO_ARG="tree,3,4"
if [ "$TOTAL_MEM_MB" -lt 6000 ]; then
  echo "⚠️  Low host memory detected (${TOTAL_MEM_MB}MB). Using smaller Mininet topology."
  TOPO_ARG="tree,3,3"
fi

# ==============================
# START ONOS
# ==============================
echo "🚀 Starting ONOS container..."

if docker ps -a --format '{{.Names}}' | grep -q "^${ONOS_CONTAINER}$"; then
    docker start "$ONOS_CONTAINER"
else
    docker run -td \
      -p 8181:8181 \
      -p 8101:8101 \
      -p 6653:6653 \
      --name "$ONOS_CONTAINER" \
      "$ONOS_IMAGE"
fi

# ==============================
# WAIT FOR ONOS
# ==============================
echo "⏳ Waiting for ONOS REST API..."
until curl -s -u onos:rocks http://127.0.0.1:8181/onos/v1/devices >/dev/null; do
    sleep 2
done
echo "✅ ONOS is up"

echo "ℹ️  NOTE: ONOS apps (openflow, fwd) must be activated ONCE via Karaf"

# ==============================
# MININET (manual start)
# The script does not start Mininet automatically; start it manually using
# the printed command below so you can control when the topology launches.
# ==============================
echo "🌐 Mininet must be started manually for this host. Run the following command in a separate terminal:"
echo
echo "sudo mn --topo ${TOPO_ARG} --controller=remote,ip=${CONTROLLER_IP},port=${OF_PORT} --switch ovs,protocols=OpenFlow13 > ${LOG_DIR}/mininet.log 2>&1 &"
echo
echo "(After starting Mininet, give it a few seconds to come up before proceeding.)"

# ==============================
# START MODULE 4
# ==============================
echo "🧠 Starting Module 4 – Congestion Detection..."
python3 controller/monitoring/congestion_detection.py \
  > "$LOG_DIR/module4.log" 2>&1 &

sleep 1

# ==============================
# START MODULE 5
# ==============================
echo "📈 Starting Module 5 – EWMA Prediction..."
python3 controller/monitoring/ewma_prediction.py \
  > "$LOG_DIR/module5.log" 2>&1 &

sleep 1

# ==============================
# START MODULE 6
# ==============================
echo "🔀 Starting Module 6 – Predictive Rerouting..."
python3 controller/routing/reroute.py \
  > "$LOG_DIR/module6.log" 2>&1 &

sleep 1

# ==============================
# START DASHBOARD
# ==============================
echo "📊 Starting Web Dashboard..."
python3 dashboard/backend.py \
  > "$LOG_DIR/dashboard.log" 2>&1 &

# After starting, if the ONOS container exited unexpectedly, show last logs for diagnostics
if docker inspect -f '{{.State.Running}}' "$ONOS_CONTAINER" 2>/dev/null | grep -q "false"; then
  echo "\n⚠️  ONOS container is not running after start. Showing last 200 lines of ONOS logs for diagnosis:\n"
  docker logs --tail 200 "$ONOS_CONTAINER" || true
fi

# ==============================
# DONE
# ==============================
echo ""
echo "✅ SYSTEM FULLY ONLINE"
echo "🌐 Dashboard → http://127.0.0.1:5000"
echo "🧠 ONOS UI  → http://127.0.0.1:8181/onos/ui"
echo ""
echo "⚠️  If this is first run:"
echo "   ssh -p 8101 karaf@127.0.0.1"
echo "   app activate org.onosproject.openflow"
echo "   app activate org.onosproject.fwd"
echo ""
