FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

# Install dependencies
RUN npm install

COPY . .

ENV PORT=3000
EXPOSE 3000

CMD ["npm", "run", "dev"]
