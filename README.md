# Secure Notes - DevSecOps Project

A secure note-taking REST API built with Flask and deployed as containerized microservices using Docker and Kubernetes. Every component — the application, secrets manager, monitoring stack, and security scanners — runs in an isolated container and communicates over a private Docker network.

## Architecture

* **Microservices**: `notes-api` (Flask), `auth-service` (Flask), `audit-service` (Flask/Elasticsearch)
* **DevSecOps Pipeline**: Jenkins, Gitleaks, SonarQube, Trivy, ZAP
* **Logging & Monitoring**: ELK Stack (Elasticsearch, Logstash, Kibana)
* **Secrets Management**: HashiCorp Vault
* **Orchestration**: Kubernetes + Horizontal Pod Autoscaler
* **Configuration Management**: Ansible

## Setup & Running Locally (Phase 1-3)

1. **Start infrastructure**
   ```bash
   docker-compose up -d
   ```
2. **Initialize Vault secrets**
   ```bash
   ./vault/vault-init.sh
   ```
3. **Services**
   - `auth-service`: http://localhost:5001
   - `notes-api`: http://localhost:5000
   - `audit-service`: http://localhost:5002
   - `kibana`: http://localhost:5601

## Jenkins Pipeline (Phase 4)

Configure a Jenkins job to point to this repository and use the provided `Jenkinsfile`.
Ensure you add the necessary credentials (`dockerhub-creds`, `sonar-token`) to Jenkins.

## Ansible Deployment (Phase 5)

The `ansible/site.yml` playbook automates the deployment of all components to the specified environments.

## Kubernetes Orchestration (Phase 6)

Apply the Kubernetes manifests to deploy the services to a K8s cluster (e.g., Minikube).

```bash
kubectl apply -f kubernetes/
```

Check autoscaling:
```bash
kubectl get hpa
```
