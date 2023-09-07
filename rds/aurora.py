from aws_cdk import core
import aws_cdk.aws_rds as rds
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_secretsmanager as secretsmanager

class AuroraStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str,
                  vpc_id:str,                 ## vpc id
                  subnet_ids:list[str],       ## list of subnet ids
                  **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a secret to store rds credentials
        rds_secret = secretsmanager.Secret(
            self, "RDSSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "mydbuser"',
                generate_string_key="password",
                exclude_characters=';=+[]{}"',
            )
        )

        # Create an Aurora Postgresql database
        database = rds.DatabaseCluster(
            self, "AuroraDatabase",
            engine=rds.DatabaseClusterEngine.AURORA_POSTGRESQL,
            credentials=rds.Credentials.from_secret(rds_secret),
            instance_props={
                "instance_type": core.InstanceType.of(
                    core.InstanceClass.BURSTABLE2, core.InstanceSize.MICRO
                ),
                "vpc": vpc_id
            }
        )

        # Create lambda function
        rds_lambda = _lambda.Function(
            self, "RDSLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda.handler",
            code=_lambda.Code.from_asset("lambda"),
            vpc=vpc_id,
            security_groups=database._security_groups,
            vpc_subnets= subnet_ids,
            environment={
                "DB_ENDPOINT": database.cluster_endpoint.hostname,
                "DB_PORT": database.cluster_endpoint.port,
                "DB_USER": "mydbuser",
                "DB_PASSWORD_SECRET": rds_secret.secret_name,  
            }
        )

        #grant lambda permissions to access database
        database.grant_connect(rds_lambda)
        database.grant_create_database(rds_lambda)

app = core.App()
AuroraStack(app, "AuroraStack")
app.synth()