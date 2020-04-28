FROM nginx:latest

RUN apt-get update
RUN apt-get install openssl

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

RUN mkdir -p /etc/nginx/ssl/ \
    && openssl req \
            -x509 \
            -subj "/C=ES/ST=Valencia/L=Valencia/O=UPV" \
            -nodes \
            -days 365 \
            -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/nginx.key \
            -out /etc/nginx/ssl/nginx.cert