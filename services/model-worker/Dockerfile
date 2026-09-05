FROM node:22-bookworm-slim
WORKDIR /app
COPY package.json ./
COPY src ./src
EXPOSE 3002
CMD ["node", "src/server.mjs"]
