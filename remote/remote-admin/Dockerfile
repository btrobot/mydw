ARG REMOTE_NODE_BASE_IMAGE=node:20-alpine
ARG REMOTE_NGINX_BASE_IMAGE=nginx:1.27-alpine
FROM ${REMOTE_NODE_BASE_IMAGE} AS build

ARG REMOTE_NPM_REGISTRY=https://registry.npmjs.org

WORKDIR /workspace/remote/remote-admin

COPY package.json package-lock.json ./
RUN npm config set registry "$REMOTE_NPM_REGISTRY" \
    && npm ci

COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
COPY public ./public

RUN npm run build && npm run build:react

FROM ${REMOTE_NGINX_BASE_IMAGE}

COPY --from=build /workspace/remote/remote-admin/dist-react /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY scripts/render-runtime-config.sh /docker-entrypoint.d/40-render-runtime-config.sh

RUN chmod +x /docker-entrypoint.d/40-render-runtime-config.sh
