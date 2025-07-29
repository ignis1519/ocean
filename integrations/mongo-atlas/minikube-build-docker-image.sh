pushd ../..
eval $(minikube -p minikube docker-env)
docker build -f ./integrations/mongo-atlas/Dockerfile --build-arg INTEGRATION_VERSION=0.0.1 --build-arg BUILD_CONTEXT=integrations/mongo-atlas -t local/port-ocean-mongo-atlas:latest .
popd
