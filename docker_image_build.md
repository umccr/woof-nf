```bash
# Set build and upload info
NAME=woof-nf
VERSION=0.0.1
URI_LOCAL="${NAME}:${VERSION}"
# AWS
AWS_PROVIDER_URL=843407916570.dkr.ecr.ap-southeast-2.amazonaws.com
AWS_URI_REMOTE="${AWS_PROVIDER_URL}/${NAME}:${VERSION}"
# Docker Hub
HUB_PROVIDER_URL=docker.io/scwatts
HUB_URI_REMOTE="${HUB_PROVIDER_URL}/${NAME}:${VERSION}"
```

```bash
docker build -t "${NAME}" -f infrastructure/Dockerfile.dependencies .
```

Upload to AWS ECR:
```bash
# Tag new image with remote AWS URI
docker tag "${NAME}" "${AWS_URI_REMOTE}"

# Configure Docker with AWS credentials and upload
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin "${AWS_PROVIDER_URL}"
docker push "${AWS_URI_REMOTE}"

# Remove unencrypted credentials
rm /Users/stephen/.docker/config.json
```

Upload to Docker Hub:
```bash
# Tag image with remote Docker Hub URI
docker tag "${NAME}" "${HUB_URI_REMOTE}"

# Configure Docker with DH credentials and upload
docker login
docker push "${HUB_URI_REMOTE}"

# Remove unencrypted credentials
rm /Users/stephen/.docker/config.json
```
