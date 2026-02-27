FROM node:20-bookworm-slim

ARG APP_NAME
ENV APP_NAME=${APP_NAME}

WORKDIR /app

COPY workspaces/web /app/workspaces/web
COPY docker/frontend/entrypoint.sh /usr/local/bin/mrq-frontend-entrypoint

RUN chmod +x /usr/local/bin/mrq-frontend-entrypoint \
    && npm ci --prefix /app/workspaces/web/${APP_NAME}

EXPOSE 3000

ENTRYPOINT ["mrq-frontend-entrypoint"]
CMD ["dev"]
