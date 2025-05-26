# Basic Next.js Dockerfile
FROM node:24-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ENV NODE_ENV=development
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
