#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# deploy-new-peers.sh
# Provisiona peer01, peer02, peer03 e peer06 no VPS.
# Pré-requisitos:
#   - DNS A records já propagados para todos os 4 hosts
#   - peer04/05/07 já rodando (usados como bootstrap de gossip)
#   - Executar como usuário kcp (com sudo NOPASSWD)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO=/dados/kcp
VENV=$REPO/sdk/python/.venv/bin/python
DATA=$REPO/data

NEW_PEERS=(peer01 peer02 peer03 peer06)
PORTS=(8801 8802 8803 8806)

EXISTING_PEERS=(
  "https://peer04.kcp-protocol.org"
  "https://peer05.kcp-protocol.org"
  "https://peer07.kcp-protocol.org"
)

echo "═══════════════════════════════════════════════════"
echo " KCP — Deploy novos peers: ${NEW_PEERS[*]}"
echo "═══════════════════════════════════════════════════"

# ── 1. Verificar DNS ──────────────────────────────────────────────────────────
echo ""
echo "▶ Verificando DNS..."
ALL_DNS_OK=true
for PEER in "${NEW_PEERS[@]}"; do
  IP=$(host ${PEER}.kcp-protocol.org 2>/dev/null | grep 'has address' | awk '{print $4}' || true)
  if [[ -z "$IP" ]]; then
    echo "  ✗ ${PEER}.kcp-protocol.org — SEM REGISTRO DNS"
    ALL_DNS_OK=false
  else
    echo "  ✓ ${PEER}.kcp-protocol.org → $IP"
  fi
done

if [[ "$ALL_DNS_OK" == "false" ]]; then
  echo ""
  echo "ERRO: Aguarde a propagação DNS antes de continuar."
  exit 1
fi

# ── 2. Criar data dirs ────────────────────────────────────────────────────────
echo ""
echo "▶ Criando data directories..."
for PEER in "${NEW_PEERS[@]}"; do
  mkdir -p $DATA/$PEER
  echo "  ✓ $DATA/$PEER"
done

# ── 3. Instalar systemd units ─────────────────────────────────────────────────
echo ""
echo "▶ Instalando systemd units..."
for PEER in "${NEW_PEERS[@]}"; do
  SRC=$REPO/infra/kcp-${PEER}.service
  DST=/etc/systemd/system/kcp-${PEER}.service
  sudo cp $SRC $DST
  sudo systemctl enable kcp-${PEER}.service
  echo "  ✓ kcp-${PEER}.service instalado e habilitado"
done
sudo systemctl daemon-reload

# ── 4. Obter certificados SSL (certbot) ───────────────────────────────────────
echo ""
echo "▶ Obtendo certificados SSL via certbot..."
DOMAINS=""
for PEER in "${NEW_PEERS[@]}"; do
  DOMAINS="$DOMAINS -d ${PEER}.kcp-protocol.org"
done
sudo certbot certonly --nginx --non-interactive --agree-tos \
  --email admin@kcp-protocol.org \
  $DOMAINS \
  --expand || {
    echo "  certbot com expand falhou — tentando por domínio individual..."
    for PEER in "${NEW_PEERS[@]}"; do
      sudo certbot certonly --nginx --non-interactive --agree-tos \
        --email admin@kcp-protocol.org \
        -d ${PEER}.kcp-protocol.org || echo "  ✗ falhou para $PEER"
    done
  }
echo "  ✓ Certificados obtidos"

# ── 5. Atualizar nginx ────────────────────────────────────────────────────────
echo ""
echo "▶ Atualizando configuração nginx..."
sudo cp $REPO/infra/nginx-kcp-peers.conf /etc/nginx/sites-available/kcp-peers
sudo nginx -t
sudo systemctl reload nginx
echo "  ✓ nginx recarregado"

# ── 6. Iniciar os novos peers ─────────────────────────────────────────────────
echo ""
echo "▶ Iniciando serviços..."
for PEER in "${NEW_PEERS[@]}"; do
  sudo systemctl start kcp-${PEER}.service
  sleep 2
  STATUS=$(systemctl is-active kcp-${PEER}.service)
  echo "  kcp-${PEER}: $STATUS"
done

# ── 7. Aguardar os peers subirem ──────────────────────────────────────────────
echo ""
echo "▶ Aguardando peers iniciarem (10s)..."
sleep 10

# ── 8. Verificar saúde dos novos peers ───────────────────────────────────────
echo ""
echo "▶ Verificando saúde dos novos peers..."
declare -A PEER_PORTS=([peer01]=8801 [peer02]=8802 [peer03]=8803 [peer06]=8806)
for PEER in "${NEW_PEERS[@]}"; do
  PORT=${PEER_PORTS[$PEER]}
  HEALTH=$(curl -s --max-time 5 http://localhost:${PORT}/kcp/v1/health 2>/dev/null || echo '{}')
  NODE_ID=$(echo $HEALTH | python3 -c "import sys,json; print(json.load(sys.stdin).get('node_id','ERRO'))" 2>/dev/null || echo "ERRO")
  echo "  $PEER (localhost:$PORT): node_id=$NODE_ID"
done

# ── 9. Cross-announce: novos peers ↔ peers existentes ────────────────────────
echo ""
echo "▶ Anunciando novos peers na rede (gossip bootstrap)..."
ALL_PORTS=(8801 8802 8803 8804 8805 8806 8807)

# Pegar node_ids de todos os peers
declare -A NODE_IDS
declare -A ALL_URLS
ALL_URLS=([8801]="https://peer01.kcp-protocol.org" [8802]="https://peer02.kcp-protocol.org"
          [8803]="https://peer03.kcp-protocol.org" [8804]="https://peer04.kcp-protocol.org"
          [8805]="https://peer05.kcp-protocol.org" [8806]="https://peer06.kcp-protocol.org"
          [8807]="https://peer07.kcp-protocol.org")
declare -A ALL_NAMES
ALL_NAMES=([8801]="KCP Public Peer 01" [8802]="KCP Public Peer 02"
           [8803]="KCP Public Peer 03" [8804]="KCP Public Peer 04"
           [8805]="KCP Public Peer 05" [8806]="KCP Public Peer 06"
           [8807]="KCP Public Peer 07")

for PORT in "${ALL_PORTS[@]}"; do
  NID=$(curl -s --max-time 5 http://localhost:${PORT}/kcp/v1/health 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('node_id',''))" 2>/dev/null || echo "")
  NODE_IDS[$PORT]=$NID
done

# Anunciar cada peer para todos os outros
for SRC_PORT in "${ALL_PORTS[@]}"; do
  for DST_PORT in "${ALL_PORTS[@]}"; do
    [[ "$SRC_PORT" == "$DST_PORT" ]] && continue
    NID=${NODE_IDS[$SRC_PORT]}
    URL=${ALL_URLS[$SRC_PORT]}
    NAME=${ALL_NAMES[$SRC_PORT]}
    [[ -z "$NID" ]] && continue
    curl -s -X POST http://localhost:${DST_PORT}/kcp/v1/peers/announce \
      -H 'Content-Type: application/json' \
      -d "{\"url\":\"$URL\",\"node_id\":\"$NID\",\"name\":\"$NAME\"}" > /dev/null 2>&1 || true
  done
done
echo "  ✓ Cross-announce concluído"

# ── 10. Status final ──────────────────────────────────────────────────────────
echo ""
echo "▶ Status final da rede:"
curl -s http://localhost:8804/kcp/v1/network-status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"  Summary: {d['summary']} ({d['online']}/{d['total']} online)\")
for p in d['peers']:
    icon = '✓' if p['status'] == 'online' else '✗'
    print(f\"  {icon} {p['name']:25} {p['url']:45} {p.get('latency_ms','?')}ms\")
"

echo ""
echo "═══════════════════════════════════════════════════"
echo " Deploy concluído!"
echo " Próximo passo: atualizar docs/peers.json com os"
echo " node_ids dos novos peers e fazer git push."
echo "═══════════════════════════════════════════════════"
