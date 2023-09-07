from aws_cdk import core
import aws_cdk.aws_rds as rds
import aws_cdk.aws_lambda as _lambda

class AuroraStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an Aurora Postgresql database
        database = rds.DatabaseCluster(
            self, "AuroraDatabase",
            engine=rds.DatabaseClusterEngine.AURORA_POSTGRESQL,
            master_user=rds.Login(
                username="admin"
                password=core.SecretValue.plain_text("password")
            ),
            instance_props={
                "instance_type": core.InstanceType.of(
                    core.InstanceClass.BURSTABLE2, core.InstanceSize.MICRO
                ),
                "vpc": <VPC_ID>,
            }
        )

        # Create lambda function
        rds_lambda = _lambda.Function(
            self, "RDSLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda.handler",
            code=_lambda.Code.from_asset("lambda"),
            vpc=<VPC_ID>,
            security_group=<SG_ID>,
            vpc_subnets=[],
            environment={
                "DB_ENDPOINT": database.cluster_endpoint.hostname,
                "DB_PORT": database.cluster_endpoint.port,
                "DB_USER": username,
                "DB_PASSWORD":  password
            }
        )

        #grant lambda permissions to access database
        database.grant_connect(rds_lambda)

app = core.App()
AuroraStack(app, "AuroraStack")
app.synth()