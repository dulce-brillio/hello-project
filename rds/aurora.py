from aws_cdk import (
    aws_rds as rds,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    Fn, Stack
)

from constructs import Construct

class AuroraStack(Stack):
    def __init__(self, scope:Construct, id: str,
                  vpc_id:str,                 ## vpc id
                  subnet_ids:list[str],       ## list of subnet ids
                  ingress_sources:list=[],
                  **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a secret to store rds credentials
        rds_secret = secretsmanager.Secret(
            self, "RDSSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "mydbuser"}',
                generate_string_key="password",
                exclude_characters=';=+[]{}"',
            )
        )

        

        azs = azs = Fn.get_azs()
        rds_vpc = ec2.Vpc.from_vpc_attributes(self, 'ExistingVPC', availability_zones=azs, vpc_id=vpc_id)
        rds_vpc_subnets = ec2.SubnetSelection(subnets=subnet_ids)

        # Create rds security group
        dbsg = ec2.SecurityGroup(self, "DatabaseSecurityGroup",
             vpc = rds_vpc,
             allow_all_outbound = True,
             description = id + " Database",
             security_group_name = id + " Database",
           )
        
        allAll = ec2.Port(protocol=ec2.Protocol("ALL"), string_representation="ALL")
        tcp5432 = ec2.Port(protocol=ec2.Protocol("TCP"), from_port=5432, to_port=5432, string_representation="tcp5432 PostgreSQL")
        tcp1433 = ec2.Port(protocol=ec2.Protocol("TCP"), from_port=1433, to_port=1433, string_representation="tcp1433 MSSQL")

        dbsg.add_ingress_rule(
        peer =dbsg,
        connection =allAll,
        description="all from self"
        )
        dbsg.add_egress_rule(
        peer =ec2.Peer.ipv4("0.0.0.0/0"),
        connection =allAll,
        description="all out"
        )

        connection_port = tcp5432
        connection_name = "tcp5432 PostgreSQL"

        for ingress_source in ingress_sources:
            dbsg.add_ingress_rule(
            peer =ingress_source,
            connection =tcp1433,
            description="tcp1433 MSSQL"
            )

        # Create an Aurora Postgresql database
        database = rds.DatabaseCluster(self, "AuroraDatabase",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_13_4),
            credentials=rds.Credentials.from_secret(rds_secret),
            instance_props={
                "instance_type": ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MEDIUM),
                "vpc": rds_vpc,
                "vpc_subnets": rds_vpc_subnets
            }
        )

        # Create lambda function
        rds_lambda = _lambda.Function(
            self, "RDSLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda.handler",
            code=_lambda.Code.from_asset("lambda"),
            vpc=rds_vpc,
            security_groups=[ec2.SecurityGroup.from_security_group_id(self,"SG",dbsg.security_group_id)],
            vpc_subnets= rds_vpc_subnets,
            environment={
                "DB_ENDPOINT": database.cluster_endpoint.hostname,
                "DB_PORT": str(database.cluster_endpoint.port),
                "DB_USER": "mydbuser",
                "DB_PASSWORD_SECRET": rds_secret.secret_name,  
            }
        )
