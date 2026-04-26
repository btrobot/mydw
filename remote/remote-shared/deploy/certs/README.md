# TLS certificate slots

When `REMOTE_DEPLOY_TLS_MODE=https`, place the certificate files here:

- `fullchain.pem`
- `privkey.pem`

They are mounted into the reverse-proxy container at:

- `/etc/nginx/certs/fullchain.pem`
- `/etc/nginx/certs/privkey.pem`

Do not commit real certificate material.
