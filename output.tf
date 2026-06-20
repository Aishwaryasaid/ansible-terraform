output "instance_details" {
    description = "Details of the created EC2 instances"
    value = {
        for name, instance in aws_instance.my_ec2_instance : name => {
            user        = var.instances[name].user
            public_ip    = instance.public_ip
                }

    }
}
