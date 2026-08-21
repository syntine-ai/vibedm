FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Expose the default TanStack Start port
EXPOSE 3000

# Start the dev server binding to all interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
