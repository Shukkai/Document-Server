# Stage 1: Build the Vue app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the source code
COPY . .

# Build the app for production
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built files to nginx public directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a custom nginx config if needed (optional)
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]