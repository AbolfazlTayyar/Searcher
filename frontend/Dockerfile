FROM node:20-slim AS build

WORKDIR /app

# Dependencies are installed before the rest of the source is copied so this
# layer is cache-hit as long as package*.json haven't changed.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines VITE_* vars into the built bundle, so the backend's browser-
# reachable URL must be known at build time, not just at container runtime.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
