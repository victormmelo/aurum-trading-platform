FROM node:22-alpine AS deps

WORKDIR /workspace/apps/web
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install

FROM node:22-alpine AS builder

WORKDIR /workspace/apps/web
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_ENV
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV
COPY --from=deps /workspace/apps/web/node_modules ./node_modules
COPY apps/web ./
RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /workspace/apps/web
ENV NODE_ENV=production
COPY --from=builder /workspace/apps/web ./

EXPOSE 3000

CMD ["npm", "run", "start"]
