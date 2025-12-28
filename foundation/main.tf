terraform {
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
  required_version = ">= 0.13"
}

provider "scaleway" {
  region = var.region
  zone   = var.zone
}

# ========================================
# REGISTRE DE CONTENEURS
# ========================================
resource "scaleway_registry_namespace" "main" {
  name        = "${var.project_name}-registry-${var.student_name}"
  description = "Registre de conteneurs pour la calculatrice"
  is_public   = false
}

# ========================================
# CLUSTER KUBERNETES
# ========================================
resource "scaleway_k8s_cluster" "main" {
  name    = "${var.project_name}-cluster-${var.student_name}"
  version = "1.29.1"
  cni     = "cilium"

  delete_additional_resources = true

  autoscaler_config {
    disable_scale_down              = false
    scale_down_delay_after_add      = "5m"
    estimator                       = "binpacking"
    expander                        = "random"
    ignore_daemonsets_utilization   = true
    balance_similar_node_groups     = true
  }
}

resource "scaleway_k8s_pool" "main" {
  cluster_id = scaleway_k8s_cluster.main.id
  name       = "${var.project_name}-pool"
  node_type  = "DEV1-M"
  size       = 2
  
  autoscaling = true
  autohealing = true
  min_size    = 1
  max_size    = 3
}

# ========================================
# BASES DE DONNÉES REDIS (par environment)
# ========================================
resource "scaleway_redis_cluster" "db" {
  for_each = toset(var.environments)

  name         = "${var.project_name}-redis-${each.value}-${var.student_name}"
  version      = "7.2.4"
  node_type    = "RED1-MICRO"
  cluster_size = 1
  
  user_name = "admin"
  password  = random_password.redis_password[each.value].result

  tags = ["environment:${each.value}", "project:${var.project_name}"]
}

# Génération de mots de passe aléatoires pour Redis
resource "random_password" "redis_password" {
  for_each = toset(var.environments)
  
  length  = 32
  special = true
}

# ========================================
# LOADBALANCERS (par environment)
# ========================================
resource "scaleway_lb" "main" {
  for_each = toset(var.environments)

  name = "${var.project_name}-lb-${each.value}-${var.student_name}"
  type = "LB-S"
  zone = var.zone

  tags = ["environment:${each.value}", "project:${var.project_name}"]
}

# ========================================
# ENTRÉES DNS (par environment)
# ========================================
resource "scaleway_domain_record" "main" {
  for_each = toset(var.environments)

  dns_zone = "polytech-dijon.kiowy.net"
  name     = each.value == "production" ? "calculatrice-${var.student_name}" : "calculatrice-dev-${var.student_name}"
  type     = "A"
  data     = scaleway_lb.main[each.value].ip_address
  ttl      = 3600
}