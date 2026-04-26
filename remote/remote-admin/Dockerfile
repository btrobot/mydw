FROM node:20-alpine AS build

WORKDIR /workspace/remote/remote-admin

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
COPY public ./public

RUN npm run build && npm run build:react

FROM nginx:1.27-alpine

COPY --from=build /workspace/remote/remote-admin/dist-react /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY scripts/render-runtime-config.sh /docker-entrypoint.d/40-render-runtime-config.sh

RUN chmod +x /docker-entrypoint.d/40-render-runtime-config.sh
