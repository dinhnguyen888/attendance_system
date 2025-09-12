# Build stage
FROM node:20-slim as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build application
RUN npm run build

# Development stage (for hot-reload during development)
FROM node:20-slim

WORKDIR /app

# Copy dependencies and source from build stage
COPY --from=build /app/node_modules ./node_modules
COPY . .

EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]