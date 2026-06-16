# Step 1: Build the Vite application
FROM node:18-alpine AS build-stage

# Set working directory inside the container
WORKDIR /app

# Copy dependency definition files
COPY package*.json ./

# Install npm packages
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Build Vite static files
RUN npm run build

# Step 2: Serve the built static files with Nginx
FROM nginx:alpine

# Copy the build artifacts from the build-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy our custom Nginx configuration to support client-side routing and proxying
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
