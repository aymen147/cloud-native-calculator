output "cluster_name" {
  description = "Nom du cluster Kubernetes"
  value       = scaleway_k8s_cluster.main.name
}

output "cluster_id" {
  description = "ID du cluster Kubernetes"
  value       = scaleway_k8s_cluster.main.id
}

output "registry_endpoint" {
  description = "Endpoint du registre de conteneurs"
  value       = scaleway_registry_namespace.main.endpoint
}

output "loadbalancer_ips" {
  description = "IPs des LoadBalancers par environment"
  value = {
    for env in var.environments :
    env => scaleway_lb.main[env].ip_address
  }
}

output "redis_endpoints" {
  description = "Endpoints Redis par environment"
  value = {
    for env in var.environments :
    env => {
      host = try(scaleway_redis_cluster.db[env].public_network[0].endpoint_address, "")
      port = try(scaleway_redis_cluster.db[env].public_network[0].endpoint_port, "")
    }
  }
  sensitive = true
}

output "dns_records" {
  description = "Enregistrements DNS créés"
  value = {
    for env in var.environments :
    env => "${scaleway_domain_record.main[env].name}.${scaleway_domain_record.main[env].dns_zone}"
  }
}

output "redis_passwords" {
  description = "Mots de passe Redis par environment"
  value = {
    for env in var.environments :
    env => random_password.redis_password[env].result
  }
  sensitive = true
}