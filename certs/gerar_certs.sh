#!/bin/bash
# Regenera todos os certificados TLS para o projeto VaccineTransport IoT
# Uso: bash gerar_certs.sh
# Requer: openssl

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=== Gerando CA ==="
cat > ca.cnf << 'EOF'
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn

[dn]
C=BR
ST=SP
L=Campinas
O=VaccineTransport
OU=IoT-Security
CN=VaccineTransport-CA
EOF

openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -config ca.cnf
echo "CA: OK"

echo "=== Gerando certificado do broker ==="
cat > broker.cnf << 'EOF'
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn

[dn]
C=BR
ST=SP
L=Campinas
O=VaccineTransport
OU=IoT-Broker
CN=10.0.0.175
EOF

cat > ext.cnf << 'EOF'
subjectAltName = IP:10.0.0.175, IP:127.0.0.1, DNS:localhost
EOF

openssl genrsa -out broker.key 2048
openssl req -new -key broker.key -out broker.csr -config broker.cnf
openssl x509 -req -days 3650 \
  -in broker.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out broker.crt -extfile ext.cnf
echo "Broker cert: OK"

echo ""
echo "Arquivos gerados:"
ls -la *.crt *.key 2>/dev/null
echo ""
echo "IMPORTANTE: Nunca commitar ca.key e broker.key no repositório!"
