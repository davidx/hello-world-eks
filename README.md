# Hello-World EKS Devops Project

#### Hello! Thank you for taking the time to review this project repository.

# What


This project aims to deploy a simple hello-world container (**application/hello_world**) onto an EKS cluster.

It uses **Pulumi** for infrastructure as code and **GitHub Actions** for CI/CD.

### Requirements
- [x] Pipeline that will deploy a "hello world" web app to Kubernetes
- [x] The CI/CD pipeline and the Kubernetes cluster are on separate systems
- [x] The web app should be accessible remotely and only with HTTPS

# How 

To deploy the infrastructure, please run the following commands:
#### Setup
```bash
brew install pulumi
pip install -r requirements.txt
```

#### Deploy the infrastructure
```bash
pulumi up --stack dev
```
This will provision an EKS cluster and a simple hello-world container onto the cluster.

The stack output 'url' will provide the URL to access the hello-world container service.

#### Generate a kubectl config:
```bash
pulumi stack -s dev output kubeconfig > ~/.aws/config
kubectl get nodes
kubectl get pods --all-namespaces
```

#### Open the URL in the browser: 
(Please accept the self-signed certificate when prompted)
```bash
pulumi stack -s dev output url 

  https://a4fa33391f0434e279b9fe74646bce93-100641608.us-west-2.elb.amazonaws.com

open `pulumi stack -s dev output url`        
```


#### CI/CD

The GitHub Actions workflows are "**Preview**" and "**Deploy**" as defined in:
- .github/workflows/preview.yml
- .github/workflows/deploy.yml

When a PR is **created**, the **preview** workflow is run.

When a PR is **merged**, the **deploy** workflow is run.

Pipeline in action: https://github.com/davidx/mh-project/actions

### Future work :

- Create multi environment pipeline with approval gate for production deployments.
- Use IRSA to authenticate from GitHub.
- S3 based pulumi remote state storage. 
- Separate out the application into its own repo and pulumi project
- Setup stack reference to share the EKS cluster between multiple projects.

