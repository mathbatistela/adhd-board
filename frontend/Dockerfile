# Stage 1: build the React bundle
FROM node:20-alpine AS build
WORKDIR /app

# Allow overriding the API URL at build time (defaults to localhost backend)
ARG VITE_API_URL="http://localhost:5000"
ENV VITE_API_URL=${VITE_API_URL}

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: serve static assets with nginx
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
