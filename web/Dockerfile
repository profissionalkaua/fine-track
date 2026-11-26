FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY scripts/install-hooks.mjs ./scripts/install-hooks.mjs
RUN npm ci
COPY web ./web
COPY scripts/next.mjs ./scripts/next.mjs
ENV PULSO_API_URL=http://api:8000
RUN npm run build

FROM node:22-bookworm-slim
ENV NODE_ENV=production
WORKDIR /app
COPY package.json package-lock.json ./
COPY scripts/install-hooks.mjs ./scripts/install-hooks.mjs
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build /app/web ./web
COPY scripts/next.mjs ./scripts/next.mjs
USER node
EXPOSE 3000
CMD ["node","node_modules/next/dist/bin/next","start","web","--hostname","0.0.0.0"]
