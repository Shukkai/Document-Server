k3d cluster create doccen --api-port 6666 -p "80:80@loadbalancer"
kubectl create configmap prometheus-config --from-file=../prometheus/prometheus.yml
kubectl create configmap grafana-datasource --from-file=../grafana/datasource.yaml
kubectl create configmap grafana-dashboard  --from-file=../grafana/dashboard.yaml --from-file=../grafana/dashboards/
kubectl apply -f deploys.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml
kubectl get pods -w