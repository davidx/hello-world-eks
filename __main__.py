
import pulumi_kubernetes as kubernetes
import pulumi_awsx as awsx
import pulumi_aws as aws
import pulumi

from helpers import (naming,
                     create_eks_service_role,
                     setup_ecr_repo,
                     setup_image,
                     setup_eks_cluster,
                     setup_instance_profiles,
                     setup_node_groups
                     )


class MoonhubDemoStack():
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.config = pulumi.Config()
        self.stack_name = pulumi.get_stack()
        self.environment_stage = self.stack_name
        self.ecr_repository = setup_ecr_repo(f"{self.name}-repo")
        self.image = setup_image(f"{self.name}-image", self.ecr_repository)
        self.vpc = awsx.ec2.Vpc(naming("vpc"))
        self.cluster_service_role = create_eks_service_role()
        self.eks_cluster = setup_eks_cluster(self.name, self.vpc, self.cluster_service_role)
        pulumi.export("kubeconfig", self.eks_cluster.kubeconfig)
        self.eks_provider = kubernetes.Provider("eksProvider", kubeconfig=self.eks_cluster.kubeconfig)

        system_instance_profile, worker_instance_profile = setup_instance_profiles()

        system_node_group, workload_node_group = setup_node_groups(self.eks_cluster,
                                                                   system_instance_profile,
                                                                   worker_instance_profile)
        # Move this to a separate repo, together with the app
        self.deployment = self.setup_deployment()
        self.service = self.setup_service()

    def setup_deployment(self):

            my_deployment = kubernetes.apps.v1.Deployment("my-deployment",
                                                          metadata=kubernetes.meta.v1.ObjectMetaArgs(
                                                              labels={
                                                                  "app": "mydeployment",
                                                              },
                                                              name="mydeployment"

                                                          ),
                                                          spec=kubernetes.apps.v1.DeploymentSpecArgs(
                                                              replicas=2,
                                                              selector=kubernetes.meta.v1.LabelSelectorArgs(
                                                                  match_labels={
                                                                      "app": "mydeployment",
                                                                  },
                                                              ),
                                                              template=kubernetes.core.v1.PodTemplateSpecArgs(
                                                                  metadata=kubernetes.meta.v1.ObjectMetaArgs(
                                                                      labels={
                                                                          "app": "mydeployment",
                                                                      },
                                                                  ),
                                                                  spec=kubernetes.core.v1.PodSpecArgs(
                                                                      containers=[kubernetes.core.v1.ContainerArgs(
                                                                          name="mydeployment",
                                                                          image=self.image.image_uri,

                                                                          ports=[kubernetes.core.v1.ContainerPortArgs(
                                                                              container_port=443)],
                                                                      )],
                                                                  ),
                                                              ),
                                                          ), opts=pulumi.ResourceOptions(depends_on=[self.eks_cluster],
                                                                                         provider=self.eks_provider))

            alb_security_group = aws.ec2.SecurityGroup("alb-sg",
                                                   vpc_id=self.vpc.vpc_id,
                                                   description="Allow HTTP and HTTPS traffic",
                                                   ingress=[
                                                       aws.ec2.SecurityGroupIngressArgs(
                                                           protocol="tcp",
                                                           from_port=443,
                                                           to_port=443,
                                                           cidr_blocks=["0.0.0.0/0"],
                                                       )],
                                                   egress=[aws.ec2.SecurityGroupEgressArgs(
                                                       protocol="-1",
                                                       from_port=0,
                                                       to_port=0,
                                                       cidr_blocks=["0.0.0.0/0"],
                                                   )],
                                                   opts=pulumi.ResourceOptions(depends_on=[self.vpc]))

    def setup_service(self):
        my_service = kubernetes.core.v1.Service("hello-world-service",
                                            spec=kubernetes.core.v1.ServiceSpecArgs(
                                                type="LoadBalancer",
                                                ports=[kubernetes.core.v1.ServicePortArgs(
                                                    port=443,
                                                    target_port=443,
                                                    protocol="TCP",
                                                )],
                                                selector={
                                                    "app": "mydeployment",
                                                },
                                            ),
                                            opts=pulumi.ResourceOptions(depends_on=[self.eks_cluster],
                                                                        provider=self.eks_provider))

        pulumi.export("kubeconfig", self.eks_cluster.kubeconfig)
        hostname = my_service.status.load_balancer.ingress[0].hostname
        pulumi.export("url", pulumi.Output.concat("https://", hostname))
        return my_service


MoonhubDemoStack("moonhub-demo-stack")