# App deployed in a Kubernetes cluster

Create K8s cluster:

```
kind create cluster
```

Create application:

```
kubectl apply -f billing-engine.yml
```

To Patch CPU value (change from 2000m to 10m):

```
kubectl edit pod billing-engine -n billing --subresource resize
```
