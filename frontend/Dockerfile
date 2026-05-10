FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN npm run build

FROM alpine:3.19 AS output
COPY --from=build /app/dist /dist
