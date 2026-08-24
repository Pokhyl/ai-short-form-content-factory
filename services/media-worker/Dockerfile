FROM node:22-alpine

RUN apk add --no-cache ffmpeg font-dejavu

WORKDIR /app

COPY package.json ./
COPY src ./src

ENV NODE_ENV=production
EXPOSE 3001

CMD ["node", "src/server.mjs"]
