# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

# Copie package.json et package-lock.json
COPY package*.json ./

# Installe les dépendances
RUN npm ci

# Copie le code source
COPY . .

# Build l'application pour la production
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copie le build depuis le stage précédent
COPY --from=build /app/dist /usr/share/nginx/html

# Copie la configuration nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose le port 80
EXPOSE 80

# Démarre nginx
CMD ["nginx", "-g", "daemon off;"]
