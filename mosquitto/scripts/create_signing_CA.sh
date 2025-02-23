#!/bin/bash

# ----------------------------------------------------------------------------------------------------------------------
# This script will create a root CA and a signing CA.  The root CA signs the signing CA's CSR to create a certificate
# for the signing CA.  The signing CA will be used to sign the server and any client CSRs.
# ----------------------------------------------------------------------------------------------------------------------
opts='/C=US/ST=Michigan/L=Ann Arbor/O=University of Michigan/OU=IT/'


cd ../certs
echo "creating private key for the root CA"
openssl genpkey -algorithm RSA -out rootCA.key -pkeyopt rsa_keygen_bits:4096
echo "creating self-signed certificate for the root CA"
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3650 -out rootCA.crt -subj "${opts}CN=Root CA"
echo  "creating private key for the signing CA"
openssl genpkey -algorithm RSA -out signingCA.key -pkeyopt rsa_keygen_bits:4096
echo "creating CSR for the signing CA"
openssl req -new -key signingCA.key -out signingCA.csr -subj "${opts}CN=Signing CA"
echo "writing signing options to file"
# Put options for having the root CA sign the signing CA's CSR into a file.  I don't know why a file is used rather \
# than providing options to the command.  Maybe it's possible; I haven't tried.
echo "[ v3_ca ]
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign" > signing_options.conf
echo "using root CA to sign the signing CA's CSR to produce a certificate for the signing CA"
openssl x509 -req -in signingCA.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out signingCA.crt -days 365 \
-sha256 -extfile signing_options.conf -extensions v3_ca
rm signing_options.conf
