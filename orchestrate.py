#!/usr/bin/env python3
"""
Orchestration script: Terraform → Inventory Generation → Ansible Playbook
Chains together terraform apply, inventory generation, and ansible playbook execution
with proper error handling and logging.
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

class Logger:
    """Simple logging utility"""
    def __init__(self, log_file="orchestration.log"):
        self.log_file = log_file
        self.start_time = datetime.now()
    
    def log(self, message, level="INFO"):
        """Log message to both console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Color coding for console output
        if level == "SUCCESS":
            colored_msg = f"{Colors.GREEN}✓ {message}{Colors.END}"
        elif level == "ERROR":
            colored_msg = f"{Colors.RED}✗ {message}{Colors.END}"
        elif level == "WARNING":
            colored_msg = f"{Colors.YELLOW}⚠ {message}{Colors.END}"
        elif level == "INFO":
            colored_msg = f"{Colors.CYAN}ℹ {message}{Colors.END}"
        else:
            colored_msg = message
        
        print(colored_msg)
        
        # Write to log file
        with open(self.log_file, "a") as f:
            f.write(log_message + "\n")
    
    def section(self, title):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
        
        with open(self.log_file, "a") as f:
            f.write(f"\n{'='*60}\n{title}\n{'='*60}\n")

logger = Logger()

def run_command(command, description):
    """
    Run a shell command and handle errors
    Returns: (success: bool, output: str)
    """
    logger.log(f"Running: {description}", "INFO")
    logger.log(f"Command: {' '.join(command)}", "INFO")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Log output
        if result.stdout:
            with open(logger.log_file, "a") as f:
                f.write(f"\n--- STDOUT ---\n{result.stdout}\n")
        
        if result.stderr:
            with open(logger.log_file, "a") as f:
                f.write(f"\n--- STDERR ---\n{result.stderr}\n")
        
        if result.returncode == 0:
            logger.log(f"{description} completed successfully", "SUCCESS")
            return True, result.stdout
        else:
            logger.log(f"{description} failed with exit code {result.returncode}", "ERROR")
            if result.stderr:
                logger.log(f"Error: {result.stderr}", "ERROR")
            return False, result.stderr
    
    except Exception as e:
        logger.log(f"Exception while running {description}: {str(e)}", "ERROR")
        return False, str(e)

def terraform_apply():
    """Step 1: Run terraform apply"""
    logger.section("STEP 1: TERRAFORM APPLY")
    
    # Change to terraform directory
    os.chdir("terraform")
    
    success, output = run_command(
        ["terraform", "apply", "-auto-approve"],
        "Terraform apply"
    )
    
    # Change back to root directory
    os.chdir("..")
    
    return success

def get_terraform_outputs():
    """Get Terraform outputs in JSON format"""
    logger.log("Fetching Terraform outputs", "INFO")
    
    # Change to terraform directory
    os.chdir("terraform")
    
    success, output = run_command(
        ["terraform", "output", "-json"],
        "Terraform output fetch"
    )
    
    # Change back to root directory
    os.chdir("..")
    
    if not success:
        logger.log("Failed to fetch Terraform outputs", "ERROR")
        return None
    
    try:
        outputs = json.loads(output)
        logger.log(f"Successfully parsed Terraform outputs", "SUCCESS")
        return outputs
    except json.JSONDecodeError as e:
        logger.log(f"Failed to parse Terraform outputs as JSON: {str(e)}", "ERROR")
        return None

def generate_inventory(terraform_outputs, inventory_file="inventory.ini"):
    """Step 2: Generate Ansible inventory from Terraform outputs"""
    logger.section("STEP 2: GENERATE ANSIBLE INVENTORY")
    
    if not terraform_outputs:
        logger.log("No Terraform outputs provided", "ERROR")
        return False
    
    try:
        # Extract instance_details from outputs
        instance_details = terraform_outputs.get("instance_details", {}).get("value", {})
        
        if not instance_details:
            logger.log("No instance details found in Terraform outputs", "ERROR")
            return False
        
        logger.log(f"Found {len(instance_details)} instances", "INFO")
        
        # Separate control node and worker nodes
        control_node = {}
        worker_nodes = {}
        
        for name, details in instance_details.items():
            if "control" in name.lower():
                control_node[name] = details
                logger.log(f"  - Control node: {name}", "INFO")
            else:
                worker_nodes[name] = details
                logger.log(f"  - Worker node: {name}", "INFO")
        
        # Build inventory content
        inventory = "[control]\n"
        
        if control_node:
            for name, details in control_node.items():
                public_ip = details.get("public_ip")
                user = details.get("user", "ec2-user")
                inventory += f"{name} ansible_host={public_ip} ansible_user={user}\n"
        
        inventory += "\n[workers]\n"
        
        if worker_nodes:
            for name, details in worker_nodes.items():
                public_ip = details.get("public_ip")
                user = details.get("user", "ec2-user")
                inventory += f"{name} ansible_host={public_ip} ansible_user={user}\n"
        
        inventory += "\n[all:vars]\n"
        inventory += "ansible_ssh_private_key_file=~/.ssh/ansible-terraform.pem\n"
        inventory += "ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n"
        
        # Write inventory to file
        try:
            with open(inventory_file, "w") as f:
                f.write(inventory)
            
            logger.log(f"Inventory file created: {inventory_file}", "SUCCESS")
            logger.log("\nGenerated inventory content:", "INFO")
            for line in inventory.split("\n"):
                if line.strip():
                    logger.log(f"  {line}", "INFO")
            
            return True
        
        except IOError as e:
            logger.log(f"Failed to write inventory file: {str(e)}", "ERROR")
            return False
    
    except Exception as e:
        logger.log(f"Error during inventory generation: {str(e)}", "ERROR")
        return False

def ansible_playbook(inventory_file="inventory.ini", playbook="playbooks/setup_nginx.yml"):
    """Step 3: Run Ansible playbook"""
    logger.section("STEP 3: RUN ANSIBLE PLAYBOOK")
    
    # Check if inventory file exists
    if not Path(inventory_file).exists():
        logger.log(f"Inventory file not found: {inventory_file}", "ERROR")
        return False
    
    logger.log(f"Using inventory: {inventory_file}", "INFO")
    logger.log(f"Using playbook: {playbook}", "INFO")
    
    # Check if playbook file exists
    if not Path(playbook).exists():
        logger.log(f"Playbook file not found: {playbook}", "ERROR")
        return False
    
    success, output = run_command(
        ["ansible-playbook", "-i", inventory_file, playbook, "-v"],
        f"Ansible playbook execution ({playbook})"
    )
    
    return success

def main():
    """Main orchestration function"""
    logger.section("INFRASTRUCTURE ORCHESTRATION STARTED")
    logger.log(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    logger.log(f"Log file: {logger.log_file}", "INFO")
    
    # Step 1: Terraform Apply
    if not terraform_apply():
        logger.log("Terraform apply failed. Stopping orchestration.", "ERROR")
        return False
    
    # Step 2: Get Terraform outputs and generate inventory
    terraform_outputs = get_terraform_outputs()
    if not terraform_outputs:
        logger.log("Failed to get Terraform outputs. Stopping orchestration.", "ERROR")
        return False
    
    if not generate_inventory(terraform_outputs):
        logger.log("Inventory generation failed. Stopping orchestration.", "ERROR")
        return False
    
    # Step 3: Run Ansible playbook
    if not ansible_playbook():
        logger.log("Ansible playbook execution failed. Stopping orchestration.", "ERROR")
        return False
    
    # Success!
    logger.section("ORCHESTRATION COMPLETED SUCCESSFULLY")
    elapsed_time = datetime.now() - logger.start_time
    logger.log(f"Total execution time: {elapsed_time}", "SUCCESS")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
