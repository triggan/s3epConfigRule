
import json
import boto3

APPLICABLE_RESOURCES = ["AWS::EC2::RouteTable"]

def contains_s3_tag(listTags):

    for tagPair in listTags:
        print(tagPair["Key"] + " " + tagPair["Value"])
        if (tagPair["Key"].lower() == "s3endpoint") and (tagPair["Value"].lower() == "true"):
            return True

    return False
#end contains_s3_tag


def contains_subnet_with_s3_access(configItem):

    #Instantiate boto3 EC2 resource for accessing subnet information
    ec2 = boto3.resource('ec2')

    #Collect all resources with a relationship to the RouteTable Configuration Item
    #(includes Subnets)
    relatedResources = configItem["relationships"]

    #Cycle through all resources from the relationships list, find subnets,
    #and see which/if a subnet has an S3Endpoint tag and if it is set to true
    for resource in relatedResources:
        print(resource["resourceId"] + " " + resource["resourceType"])
        if resource["resourceType"] == "AWS::EC2::Subnet":
            subnet = ec2.Subnet(resource["resourceId"])
            print ("Subnet tags: " + str(len(subnet.tags)))
            if contains_s3_tag(subnet.tags):
                return True

    return False
#end contains_subnet_with_s3_access


def lambda_handler(event, context):

    invoking_event = json.loads(event["invokingEvent"])
    configuration_item = invoking_event["configurationItem"]
    rule_parameters = json.loads(event["ruleParameters"])

    result_token = "No token found."
    if "resultToken" in event:
        result_token = event["resultToken"]

    if configuration_item["resourceType"] in APPLICABLE_RESOURCES:
        #print("Configuration Change of a Subnet Detected! - " + json.dumps(configuration_item))
        if contains_subnet_with_s3_access(configuration_item):
            evaluation = { "compliance_type": "COMPLIANT" }
        else:
            evaluation = { "compliance_type": "NOT_APPLICABLE" }

    config = boto3.client("config")
    config.put_evaluations(
        Evaluations=[
            {
                "ComplianceResourceType":
                    configuration_item["resourceType"],
                "ComplianceResourceId":
                    configuration_item["resourceId"],
                "ComplianceType":
                    evaluation["compliance_type"],
#               "Annotation":
#                   evaluation["annotation"],
                "OrderingTimestamp":
                    configuration_item["configurationItemCaptureTime"]
            },
        ],
        ResultToken=result_token
    )
