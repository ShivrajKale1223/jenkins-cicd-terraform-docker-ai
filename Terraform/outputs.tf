output "jenkins_url" {
  value = "http://${aws_instance.jenkins.public_ip}:8080"
}

output "app_url" {
  value = "http://${aws_instance.jenkins.public_ip}"
}

output "ecr_repo_url" {
  value = aws_ecr_repository.app.repository_url
}

output "instance_id" {
  value = aws_instance.jenkins.id
}