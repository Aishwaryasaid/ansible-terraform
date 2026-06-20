resource "aws_instance" "my_ec2_instance" {

    for_each = var.instances
    ami           = each.value.ami
    instance_type  = each.value.instance_type
    key_name       = aws_key_pair.my_key_pair.key_name
    vpc_security_group_ids = [aws_security_group.ansible_lab.id]
    root_block_device {

        volume_size = each.value.volume_size
    }
    tags = {
        Name = each.value.user
        Managedby = "Terraform"


    }        

     depends_on = [aws_security_group.ansible_lab, aws_key_pair.my_key_pair]
    }   
