from aws_cdk import (
    aws_rds as rds,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    aws_iam as iam,
    custom_resources as cr,
    Stack
)

from constructs import Construct

class AuroraStack(Stack):
    def __init__(self, scope:Construct, id: str,
                  rds_vpc:ec2.Vpc,                 ## vpc id
                  #subnet_ids:list[str],       ## list of subnet ids
                  ingress_sources:list=[],
                  **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Create a secret to store rds credentials
        rds_secret = secretsmanager.Secret(
            self, "RDSSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "mydbuser"}',
                generate_string_key="password",
                exclude_characters='/@;=+[]{}"',
            )
        )
        
        # Create an Aurora Postgresql database
        database = rds.DatabaseCluster(self, "AuroraDatabase",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_13_4),
            credentials=rds.Credentials.from_secret(rds_secret),
            instance_props={
                "instance_type": ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MEDIUM),
                "vpc": rds_vpc,
                "vpc_subnets": ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
            },
        )

        proxy = rds.DatabaseProxy(self, "Proxy",
            proxy_target=rds.ProxyTarget.from_cluster(database),
            secrets=[rds_secret],
            vpc=rds_vpc
        )

        lambda_role = iam.Role(self, "DBProxyRole", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"))
        proxy.grant_connect(lambda_role, "admin")

        # Instance Role and SSM Managed Policy
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        ec2_security_group = ec2.SecurityGroup(self, "Ec2SecurityGroup", vpc=rds_vpc)
        database.connections.allow_from(
            ec2_security_group,
            ec2.Port.tcp(5432),
            "Allow inbound from EC2"
        )
        
        lambdaLayer = _lambda.LayerVersion(self, 'lambda-layer',
                  code = _lambda.AssetCode('lambda/layer/'),
                  compatible_runtimes = [_lambda.Runtime.PYTHON_3_9],
        )

        # Create lambda function
        rds_lambda = _lambda.Function(
            self, "RDSLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda/code"),
            layers=[lambdaLayer],
            vpc=rds_vpc,
            security_groups=[ec2.SecurityGroup.from_security_group_id(self,"SG",ec2_security_group.security_group_id)],
            vpc_subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            environment={
                "DB_ENDPOINT": database.cluster_endpoint.hostname,
                "DB_PORT": str(database.cluster_endpoint.port),
                "DB_USER": "mydbuser",
                "DB_PASSWORD_SECRET": rds_secret.secret_name,  
            },
            role=lambda_role
        )

        rds_secret.grant_read(rds_lambda)

        invoke_lambda_resource = cr.AwsCustomResource(
            self,
            "InvokeLambdaResource",
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "lambda:InvokeFunction"
                    ],
                    resources=[rds_lambda.function_arn]
                )
            ]),
            on_create={
                "service": "Lambda",
                "action": "invoke",
                "parameters": {
                    "FunctionName": rds_lambda.function_name,
                    "InvocationType": "RequestResponse",
                },
                "physical_resource_id": cr.PhysicalResourceId.from_response("Payload"),
            },
        )

        # AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
            )

        # Instance
        instance = ec2.Instance(self, "Instance",
            instance_type=ec2.InstanceType("t3.nano"),
            machine_image=amzn_linux,
            vpc = rds_vpc,
            vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            role = role,
            security_group = ec2_security_group
            )
