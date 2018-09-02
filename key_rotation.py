import boto3
from botocore.exceptions import ClientError
import sys


ec2 = boto3.client('ec2')
ec2_create = boto3.resource('ec2')
waiter_img_avail = ec2.get_waiter('image_available')
waiter_img_exist = ec2.get_waiter('image_exists')

instance_id = sys.argv[2]
key_pair = sys.argv[3]

image_name='Image for '+instance_id

def describe_instance(instance_id):
    try:
        response=ec2.describe_instances(InstanceIds=[instance_id])
        return response
    except ClientError as e:
        print(e)

def create_image(instance_id):
    print "Creating Image for InstanceId :"+instance_id;
    try:
        image_creation=ec2.create_image(
            Description='Image for '+instance_id,
            InstanceId=instance_id,
            Name=image_name,
            NoReboot=True
        )
        waiter_img_avail.wait(Filters=[{'Name': 'name','Values':[image_name]}])
        return True

    except ClientError as e:
        print(e)

def is_image_available(image_name):
    try:
        waiter_img_exist.wait(Filters=[{'Name': 'name','Values':[image_name]}])
    except Exception, e:
        print e

def getAMIid(image_name):
    try:
        image_details=ec2.describe_images(Filters=[{'Name': 'name','Values':[image_name]}])
        return image_details['Images']
    except ClientError as e:
        print(e)

def create_instance(ami_id, key_name, instance_type,subnet_id, security_groups,tags):
    print "Launching Instance using AMI";
    try:
        launch_instance=ec2_create.create_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MaxCount=1,
            MinCount=1,
            SecurityGroupIds=security_groups,
            SubnetId=subnet_id,
            TagSpecifications = [{
                'ResourceType': 'instance',
                'Tags': tags
                                },
                            ],
        )
        return launch_instance
    except ClientError as e:
        print(e)

#Main Function
if sys.argv[1] == '--modify-instance':

    print "Getting first Instance Details..."
    instance_detail = describe_instance(instance_id)
    instance_type = instance_detail['Reservations'][0]['Instances'][0]['InstanceType']
    subnet_id = instance_detail['Reservations'][0]['Instances'][0]['SubnetId']
    security_groups = instance_detail['Reservations'][0]['Instances'][0]['SecurityGroups']
    tags = instance_detail['Reservations'][0]['Instances'][0]['Tags']
    group_ids = []
    for security_groups_ids in security_groups:
        group_ids.append(security_groups_ids['GroupId'])

    for instance in instance_detail['Reservations'][0]['Instances'][0]['Tags']:
        if 'Key' in instance:
            if instance['Key'] != 'aws:autoscaling:groupName' and instance['Value'] != '':
                if not getAMIid(image_name):
                    create_image(instance_id)
                    get_image_id = getAMIid(image_name)
                    create_instance(ami_id=get_image_id[0]['ImageId'], key_name='Server-Key', instance_type=instance_type,subnet_id=subnet_id, security_groups=group_ids, tags=tags)
                    break
                else:
                    get_image_id = getAMIid(image_name)
                    create_instance(ami_id=get_image_id[0]['ImageId'], key_name='Server-Key', instance_type=instance_type,subnet_id=subnet_id, security_groups=group_ids, tags=tags)
                    break
        else:
            print "Don't need to create image because the instance belongs to auto scaling group"

else:
    print "Please select appropiate option i.e --modify-instance [instance_id] [key_pair_name]"
