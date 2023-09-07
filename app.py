#!/usr/bin/env python3
import os

import aws_cdk as cdk

#from hello_project.hello_project_stack import HelloProjectStack
from ec2.ec2 import EC2InstanceStack
from rds.aurora import AuroraStack

app = cdk.App()
ec2_stack = EC2InstanceStack(app, "EC2InstanceStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )


AuroraStack(app, "AuroraStack", description="Aurora Postgresql Cluster",
  vpc_id    = ec2_stack.vpc.vpc_id,
  subnet_ids= ec2_stack.vpc.public_subnets,
)

app.synth()
