FROM nginx:stable

# DEFAULT ARGS that can be changed
ARG PROXY_DOMAIN="example.com"

# set environment variables for site config generation
ENV PROXY_DOMAIN=$PROXY_DOMAIN
ENV DOLLAR='$'

COPY nginx.conf /etc/nginx/nginx.conf
COPY nginxconfig.io/ /etc/nginx/nginxconfig.io/

# generate site config
COPY sites-available/example.com.conf /etc/nginx/sites-available/${PROXY_DOMAIN}.conf.template
RUN envsubst < /etc/nginx/sites-available/${PROXY_DOMAIN}.conf.template > /etc/nginx/sites-available/${PROXY_DOMAIN}.conf

# enable site
RUN ln -s /etc/nginx/sites-available/${PROXY_DOMAIN}.conf /etc/nginx/sites-enabled/${PROXY_DOMAIN}.conf