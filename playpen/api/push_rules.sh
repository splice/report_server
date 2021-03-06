#!/bin/sh

export SERVER_ADDR=`hostname`
export PORT=8000
export CA_CERT=/etc/pki/splice/generated/Splice_HTTPS_CA.cert
export CLIENT_CERT=/etc/pki/consumer/Splice_identity.cert
export CLIENT_KEY=/etc/pki/consumer/Splice_identity.key
export SAMPLE_JSON=./rules.json

#curl -s -S --cacert ${CA_CERT} --cert ${CLIENT_CERT} --key ${CLIENT_KEY} --dump-header - -H "Content-Type: application/json" -X POST --data @${SAMPLE_JSON} https://${SERVER_ADDR}:${PORT}/api/v1/rules/  --trace-ascii curl_log

curl --dump-header - -H "Content-Type: application/json" -X POST --data @${SAMPLE_JSON} http://${SERVER_ADDR}:${PORT}/report-server/api/v1/rules/  --trace-ascii curl_log
