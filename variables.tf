
# aws region
variable "aws_region" {
  type        = string
  description = "The AWS region where resources will be created."
  default     = "us-west-2" # Optional default value
}

# instance type
# variable "instance_type" {
#   type        = string
#   description = "The type of EC2 instance to launch."
#     default     = "t2.micro" # Optional default value           
# }

# # Volume size
# variable "volume_size" {
#   type        = number
#   description = "The size of the EBS volume in GB."
#   default     = 10 # Optional default value
# }

#ssh key path
variable "ssh_key_path" {
  type        = string
  description = "The file path to the SSH private key for accessing the EC2 instance."
  default     = "~/.ssh/ansible-terraform" # Optional default value
}


#key pair name
variable "key_name" {
  type        = string
  description = "The name of the SSH key pair to use for the EC2 instance."
  default     = "ansible-terraform" # Optional default value
}

#instance

variable "instances"{
    type = map(object({
        user           = string
        ami            = string
        instance_type   = string
        volume_size     = number
  
  
    }))
    description = "A list of EC2 instances to create with their respective configurations."

    # default value for instances
    default = {
      "control-node" = {
            user           = "control-node"
            ami            = "ami-02167eae61967e403"
            instance_type   = "t2.micro"
            volume_size     = 10
           
        }, 
          "worker-node-1" = {
            user           = "worker-node-1"
            ami            = "ami-02167eae61967e403"
            instance_type   = "t2.micro"
            volume_size     = 10
        },
          "worker-node-2" ={
            user           = "worker-node-2"
            ami            = "ami-02167eae61967e403"
            instance_type   = "t2.micro"
            volume_size     = 10
        }

       
    }  
}