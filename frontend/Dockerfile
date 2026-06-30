FROM node:20-alpine

WORKDIR /app

# Install dependencies first for caching
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the application files
COPY . .

# Set dynamic API URL env variable for Next.js build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# Build Next.js application
RUN npm run build

EXPOSE 3010

# Start server
CMD ["npx", "next", "start", "-p", "3010"]
