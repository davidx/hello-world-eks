
import pulumi
import json
import pulumi_aws as aws
import pulumi_awsx as awsx
import pulumi_eks as eks
import sys


def naming(thing):
    project_name = pulumi.get_project()
    environment_stage = pulumi.get_stack()
    return f"{project_name}-{thing}-{environment_stage}"

def debug_python_executable():
    print("Using this Python:")
    print(sys.executable)


def create_eks_service_role():
    eks_service_role = aws.iam.Role(naming("eksServiceRole"),
                                    assume_role_policy=json.dumps({
                                        "Version": "2012-10-17",
                                        "Statement": [{
                                            "Effect": "Allow",
                                            "Principal": {
                                                "Service": "eks.amazonaws.com"
                                            },
                                            "Action": "sts:AssumeRole"
                                        }]
                                    })
                                    )

    aws.iam.RolePolicyAttachment(naming("eksServiceRole-policy"),
                                 role=eks_service_role.name,
                                 policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
                                 )
    return eks_service_role

def setup_ecr_repo(name):
    return awsx.ecr.Repository(
        name,
        awsx.ecr.RepositoryArgs(
            force_delete=True
        ),
    )
def setup_image(name, repository):

    return awsx.ecr.Image(
        name,
        repository_url=repository.url,
        context="./application/hello_world",
        platform="amd64",
    )
def setup_eks_cluster(name, vpc, cluster_service_role):
    config = pulumi.Config()
    return eks.Cluster(naming(name),
                          version=config.require("eks_version"),
                          service_role=cluster_service_role,
                          desired_capacity=1,
                          min_size=1,
                          max_size=1,
                          enabled_cluster_log_types=[
                              "api",
                              "audit",
                              "authenticator",
                          ],
                          vpc_id=vpc.vpc_id,
                          public_subnet_ids=vpc.public_subnet_ids,
                          private_subnet_ids=vpc.private_subnet_ids,
                          node_associate_public_ip_address=False
                          )
def setup_instance_profiles():
    managed_policy_arns = [
        "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
        "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    ]
    assume_role_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com",
            },
        }],
    })
    sys_role = aws.iam.Role("system-role",
                            assume_role_policy=assume_role_policy,
                            managed_policy_arns=managed_policy_arns)
    worker_role = aws.iam.Role("worker-role",
                               assume_role_policy=assume_role_policy,
                               managed_policy_arns=managed_policy_arns)
    system_instance_profile = aws.iam.InstanceProfile("system_instance_profile", role=sys_role.name)
    worker_instance_profile = aws.iam.InstanceProfile("worker_instance_profile", role=worker_role.name)
    return system_instance_profile, worker_instance_profile

def setup_node_groups(eks_cluster, system_instance_profile, worker_instance_profile):
    config=pulumi.Config()
    system_node_group = eks.NodeGroupV2("systemNodeGroup",
                                        cluster=eks_cluster,
                                        instance_type=config.require("eks_instance_type"),
                                        instance_profile=system_instance_profile,
                                        desired_capacity=1,
                                        min_size=1,
                                        max_size=1,
                                        labels={
                                            "node-type": "system",
                                        })

    workload_node_group = eks.NodeGroupV2("workloadNodeGroup",
                                          cluster=eks_cluster,
                                          instance_type=config.require("eks_instance_type"),
                                          instance_profile=worker_instance_profile,
                                          desired_capacity=config.require_int("eks_desired_capacity"),
                                          min_size=config.require_int("eks_min_size"),
                                          max_size=config.require_int("eks_max_size"),

                                          labels={
                                              "node-type": "workload",
                                          })
    return system_node_group, workload_node_group
