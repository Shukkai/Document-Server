k3d cluster create cn-doc --api-port 6666 -p "80:80@loadbalancer"
kubectl apply -f deploys.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml
kubectl get pods -w