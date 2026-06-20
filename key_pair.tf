# 1. Generate the key pair resource
resource "tls_private_key" "example" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# 2. Reference the public key directly from the resource memory, NOT the file system
resource "aws_key_pair" "my_key_pair" {
  key_name   = var.key_name
  public_key = tls_private_key.example.public_key_openssh 
}

# 3. Optional: Save it to disk for Ansible to use later
resource "local_file" "private_key" {
  content  = tls_private_key.example.private_key_pem
  filename = "${path.module}/terraform-ansible.pem"
}


