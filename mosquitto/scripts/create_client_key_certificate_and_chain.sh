#!/bin/bash

# ----------------------------------------------------------------------------------------------------------------------
# Create the client's key and certificate along with a chain of certificates in a common directory to be used by a
# MQTTClient object.
# ----------------------------------------------------------------------------------------------------------------------
# This directory will be created and all files produced here will be written into it.
client_certs_dir="$(pwd)/client_certs"
opts='/C=US/ST=Michigan/L=Ann Arbor/O=University of Michigan/OU=IT/'

# verify that a script was provided as an argument
if [ -z "$1" ] || [ "$1" == '' ]
then
  echo "A username for the client certificate needs to provided as an argument."
  exit 1
else
  username="$1"
fi

mkdir client_certs
echo "creating a chain of certificates"
cat ../certs/server.crt ../certs/signingCA.crt ../certs/rootCA.crt > "${client_certs_dir}"/chain.crt
echo "creating private key for the client"
openssl genpkey -algorithm RSA -out "${client_certs_dir}"/client.key -pkeyopt rsa_keygen_bits:2048
echo "creating CSR for the client"
openssl req -new -key "${client_certs_dir}"/client.key -out "${client_certs_dir}"/client.csr -subj "${opts}CN=${username}"
echo "using the signing CA to sign the client's CSR to create a certificate for the client"
openssl x509 -req -in "${client_certs_dir}"/client.csr -CA ../certs/signingCA.crt -CAkey ../certs/signingCA.key \
-CAcreateserial -out "${client_certs_dir}"/client.crt -days 825 -sha256

