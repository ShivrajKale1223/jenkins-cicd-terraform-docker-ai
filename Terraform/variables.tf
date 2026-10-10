variable "region" {
  type    = string
  default = "us-west-2"
}

variable "project" {
  type    = string
  default = "myapp"
}

variable "my_ip" {
  description = "Your public IP in CIDR form, e.g. 1.2.3.4/32"
  type        = string
}

variable "key_name" {
  description = "EC2 key pair name for SSH"
  type        = string
  default     = "Oregon-key"
}