# Foundation - Infrastructure Terraform

> Infrastructure as Code pour la Calculatrice Cloud Native

---

## 📋 Table des matières

- [Description](#description)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Structure du projet](#structure-du-projet)
- [Variables](#variables)
- [Ressources créées](#ressources-créées)
- [Utilisation](#utilisation)
- [Plan Terraform](#plan-terraform)
- [Outputs](#outputs)
- [Notes importantes](#notes-importantes)

---

## 🎯 Description

Ce dossier contient la configuration Terraform pour provisionner l'infrastructure cloud sur **Scaleway** nécessaire au déploiement de la calculatrice cloud-native.

L'infrastructure est définie comme **Infrastructure as Code (IaC)** permettant :
- ✅ **Reproductibilité** : Créer/détruire l'infrastructure à volonté
- ✅ **Versioning** : Suivi des changements dans Git
- ✅ **Documentation** : Le code est la documentation
- ✅ **Collaboration** : Partage facile entre développeurs

---

## 🏗️ Architecture

### Vue d'ensemble
```
┌─────────────────────────────────────────────────────┐
│                   INTERNET                          │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│ DNS Production │    │ DNS Development │
│ calculatrice-  │    │ calculatrice-   │
│ aymenbenchaaba-│    │ dev-aymenbench- │
│ ne.polytech... │    │ aabane.poly...  │
└───────┬────────┘    └────────┬────────┘
        │                      │
┌───────▼────────┐    ┌────────▼────────┐
│ LoadBalancer   │    │ LoadBalancer    │
│   Production   │    │  Development    │
└───────┬────────┘    └────────┬────────┘
        │                      │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────┐
        │  Cluster Kubernetes │
        │    (2-3 nodes)      │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐  ┌────────▼────────┐
│ Redis          │  │ Container       │
│ Production     │  │ Registry        │
└────────────────┘  └─────────────────┘
        │
┌───────▼────────┐
│ Redis          │
│ Development    │
└────────────────┘
```

### Environnements

L'infrastructure supporte **2 environnements isolés** :

| Environment | URL | LoadBalancer | Redis | Usage |
|-------------|-----|--------------|-------|-------|
| **Production** | `calculatrice-aymenbenchaabane.polytech-dijon.kiowy.net` | LB PROD | Redis PROD | Utilisateurs réels |
| **Development** | `calculatrice-dev-aymenbenchaabane.polytech-dijon.kiowy.net` | LB DEV | Redis DEV | Tests et développement |

---

## 📦 Prérequis

### Logiciels requis

- [Terraform](https://www.terraform.io/downloads) >= 0.13
- [Git](https://git-scm.com/) (pour versionner)

### Compte Scaleway (optionnel pour validation)

Pour exécuter `terraform fmt`, `terraform validate` et `terraform plan`, **aucun compte Scaleway n'est nécessaire**.

Pour déployer réellement (`terraform apply`), vous aurez besoin de :
- Un compte Scaleway
- Les variables d'environnement configurées :
```bash
  export SCW_ACCESS_KEY="<access-key>"
  export SCW_SECRET_KEY="<secret-key>"
  export SCW_DEFAULT_PROJECT_ID="<project-id>"
```

---

## 📁 Structure du projet
```
foundation/
├── README.md              # Ce fichier
├── main.tf                # Ressources principales
├── variables.tf           # Définition des variables
├── terraform.tfvars       # Valeurs des variables
├── outputs.tf             # Valeurs de sortie
├── .terraform/            # Dossier Terraform (généré)
├── .terraform.lock.hcl    # Lock des providers
└── plan-output.txt        # Résultat du plan (optionnel)
```

---

## ⚙️ Variables

### Fichier `variables.tf`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `project_name` | string | `"calculator"` | Nom du projet |
| `student_name` | string | - | Nom de l'étudiant (obligatoire) |
| `environments` | list(string) | `["production", "development"]` | Liste des environnements |
| `region` | string | `"fr-par"` | Région Scaleway |
| `zone` | string | `"fr-par-1"` | Zone Scaleway |

### Fichier `terraform.tfvars`
```hcl
student_name = "aymenbenchaabane"
```

---

## 🔧 Ressources créées

### Récapitulatif

| Ressource | Quantité | Description |
|-----------|----------|-------------|
| Cluster Kubernetes | 1 | Cluster K8s version 1.29.1 avec CNI Cilium |
| Pool de nodes | 1 | 2-3 nodes DEV1-M avec autoscaling |
| Registre de conteneurs | 1 | Stockage privé des images Docker |
| Redis (managé) | 2 | 1 par environnement (prod + dev) |
| LoadBalancer | 2 | 1 par environnement (prod + dev) |
| Entrées DNS | 2 | 1 par environnement (prod + dev) |
| Mots de passe aléatoires | 2 | 1 par Redis (sécurisés, 32 caractères) |

**Total : 11 ressources**

---

### Détails des ressources

#### 1. Cluster Kubernetes
```hcl
resource "scaleway_k8s_cluster" "main"
```

- **Version** : 1.29.1
- **CNI** : Cilium
- **Autoscaling** : Activé
- **Nom** : `calculator-cluster-aymenbenchaabane`

**Fonctionnalités** :
- Scale down automatique après 5 minutes
- Suppression des ressources additionnelles à la destruction
- Estimateur binpacking pour optimiser l'allocation

#### 2. Pool de nodes
```hcl
resource "scaleway_k8s_pool" "main"
```

- **Type de node** : DEV1-M (2 vCPU, 4GB RAM)
- **Taille initiale** : 2 nodes
- **Min** : 1 node
- **Max** : 3 nodes
- **Autoscaling** : ✅ Activé
- **Autohealing** : ✅ Activé

#### 3. Registre de conteneurs
```hcl
resource "scaleway_registry_namespace" "main"
```

- **Nom** : `calculator-registry-aymenbenchaabane`
- **Visibilité** : Privé
- **Usage** : Stockage des images Docker (backend, frontend, consumer)

#### 4. Redis (par environnement)
```hcl
resource "scaleway_redis_cluster" "db"
```

- **Version** : 7.2.4
- **Type de node** : RED1-MICRO
- **Cluster size** : 1
- **User** : admin
- **Password** : Généré aléatoirement (32 caractères)

**Noms** :
- Production : `calculator-redis-production-aymenbenchaabane`
- Development : `calculator-redis-development-aymenbenchaabane`

#### 5. LoadBalancer (par environnement)
```hcl
resource "scaleway_lb" "main"
```

- **Type** : LB-S (Small)
- **Zone** : fr-par-1

**Noms** :
- Production : `calculator-lb-production-aymenbenchaabane`
- Development : `calculator-lb-development-aymenbenchaabane`

#### 6. DNS (par environnement)
```hcl
resource "scaleway_domain_record" "main"
```

- **Zone DNS** : `polytech-dijon.kiowy.net`
- **Type** : A
- **TTL** : 3600

**Noms** :
- Production : `calculatrice-aymenbenchaabane`
- Development : `calculatrice-dev-aymenbenchaabane`

---

## 🚀 Utilisation

### 1. Initialisation

Télécharge les providers nécessaires :
```bash
cd foundation
terraform init
```

**Sortie attendue** :
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/random versions matching "~> 3.5"...
- Finding latest version of scaleway/scaleway...
Terraform has been successfully initialized!
```

---

### 2. Formatage du code

Formate automatiquement les fichiers `.tf` :
```bash
terraform fmt
```

---

### 3. Validation

Vérifie la syntaxe et la cohérence :
```bash
terraform validate
```

**Sortie attendue** :
```
Success! The configuration is valid.
```

---

### 4. Plan

Affiche les changements qui seront appliqués :
```bash
terraform plan
```

Pour sauvegarder le plan :
```bash
terraform plan -out=tfplan
```

Pour générer un fichier texte :
```bash
terraform plan > plan-output.txt
```

---

### 5. Application (déploiement réel)

⚠️ **Attention** : Cette commande crée réellement les ressources (coût financier)
```bash
terraform apply
```

Pour appliquer un plan sauvegardé :
```bash
terraform apply tfplan
```

---

### 6. Destruction

Pour supprimer toutes les ressources :
```bash
terraform destroy
```

---

## 📊 Plan Terraform

Résultat de `terraform plan` exécuté le 27/12/2025 :
```
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the
following symbols:
  + create

Terraform will perform the following actions:

  # random_password.redis_password["development"] will be created
  + resource "random_password" "redis_password" {
      + bcrypt_hash = (sensitive value)
      + id          = (known after apply)
      + length      = 32
      + lower       = true
      + min_lower   = 0
      + min_numeric = 0
      + min_special = 0
      + min_upper   = 0
      + number      = true
      + numeric     = true
      + result      = (sensitive value)
      + special     = true
      + upper       = true
    }

  # random_password.redis_password["production"] will be created
  + resource "random_password" "redis_password" {
      + bcrypt_hash = (sensitive value)
      + id          = (known after apply)
      + length      = 32
      + lower       = true
      + min_lower   = 0
      + min_numeric = 0
      + min_special = 0
      + min_upper   = 0
      + number      = true
      + numeric     = true
      + result      = (sensitive value)
      + special     = true
      + upper       = true
    }

  # scaleway_domain_record.main["development"] will be created
  + resource "scaleway_domain_record" "main" {
      + data       = (known after apply)
      + dns_zone   = "polytech-dijon.kiowy.net"
      + fqdn       = (known after apply)
      + id         = (known after apply)
      + name       = "calculatrice-dev-aymenbenchaabane"
      + priority   = (known after apply)
      + project_id = (known after apply)
      + root_zone  = (known after apply)
      + ttl        = 3600
      + type       = "A"
    }

  # scaleway_domain_record.main["production"] will be created
  + resource "scaleway_domain_record" "main" {
      + data       = (known after apply)
      + dns_zone   = "polytech-dijon.kiowy.net"
      + fqdn       = (known after apply)
      + id         = (known after apply)
      + name       = "calculatrice-aymenbenchaabane"
      + priority   = (known after apply)
      + project_id = (known after apply)
      + root_zone  = (known after apply)
      + ttl        = 3600
      + type       = "A"
    }

  # scaleway_k8s_cluster.main will be created
  + resource "scaleway_k8s_cluster" "main" {
      + apiserver_url               = (known after apply)
      + cni                         = "cilium"
      + created_at                  = (known after apply)
      + delete_additional_resources = true
      + id                          = (known after apply)
      + kubeconfig                  = (sensitive value)
      + name                        = "calculator-cluster-aymenbenchaabane"
      + organization_id             = (known after apply)
      + pod_cidr                    = (known after apply)
      + project_id                  = (known after apply)
      + service_cidr                = (known after apply)
      + service_dns_ip              = (known after apply)
      + status                      = (known after apply)
      + type                        = (known after apply)
      + updated_at                  = (known after apply)
      + upgrade_available           = (known after apply)
      + version                     = "1.29.1"
      + wildcard_dns                = (known after apply)

      + auto_upgrade (known after apply)

      + autoscaler_config {
          + balance_similar_node_groups      = true
          + disable_scale_down               = false
          + estimator                        = "binpacking"
          + expander                         = "random"
          + expendable_pods_priority_cutoff  = -10
          + ignore_daemonsets_utilization    = true
          + max_graceful_termination_sec     = 600
          + scale_down_delay_after_add       = "5m"
          + scale_down_unneeded_time         = "10m"
          + scale_down_utilization_threshold = 0.5
        }

      + open_id_connect_config (known after apply)
    }

  # scaleway_k8s_pool.main will be created
  + resource "scaleway_k8s_pool" "main" {
      + autohealing            = true
      + autoscaling            = true
      + cluster_id             = (known after apply)
      + container_runtime      = "containerd"
      + created_at             = (known after apply)
      + current_size           = (known after apply)
      + id                     = (known after apply)
      + max_size               = 3
      + min_size               = 1
      + name                   = "calculator-pool"
      + node_type              = "DEV1-M"
      + nodes                  = (known after apply)
      + public_ip_disabled     = false
      + root_volume_size_in_gb = (known after apply)
      + root_volume_type       = (known after apply)
      + security_group_id      = (known after apply)
      + size                   = 2
      + status                 = (known after apply)
      + updated_at             = (known after apply)
      + version                = (known after apply)
      + wait_for_pool_ready    = true

      + upgrade_policy (known after apply)
    }

  # scaleway_lb.main["development"] will be created
  + resource "scaleway_lb" "main" {
      + external_private_networks = false
      + id                        = (known after apply)
      + ip_address                = (known after apply)
      + ip_id                     = (known after apply)
      + ip_ids                    = (known after apply)
      + ipv6_address              = (known after apply)
      + name                      = "calculator-lb-development-aymenbenchaabane"
      + organization_id           = (known after apply)
      + private_ips               = (known after apply)
      + project_id                = (known after apply)
      + region                    = (known after apply)
      + ssl_compatibility_level   = "ssl_compatibility_level_intermediate"
      + tags                      = [
          + "environment:development",
          + "project:calculator",
        ]
      + type                      = "LB-S"

      + private_network (known after apply)
    }

  # scaleway_lb.main["production"] will be created
  + resource "scaleway_lb" "main" {
      + external_private_networks = false
      + id                        = (known after apply)
      + ip_address                = (known after apply)
      + ip_id                     = (known after apply)
      + ip_ids                    = (known after apply)
      + ipv6_address              = (known after apply)
      + name                      = "calculator-lb-production-aymenbenchaabane"
      + organization_id           = (known after apply)
      + private_ips               = (known after apply)
      + project_id                = (known after apply)
      + region                    = (known after apply)
      + ssl_compatibility_level   = "ssl_compatibility_level_intermediate"
      + tags                      = [
          + "environment:production",
          + "project:calculator",
        ]
      + type                      = "LB-S"

      + private_network (known after apply)
    }

  # scaleway_redis_cluster.db["development"] will be created
  + resource "scaleway_redis_cluster" "db" {
      + certificate  = (known after apply)
      + cluster_size = 1
      + created_at   = (known after apply)
      + id           = (known after apply)
      + name         = "calculator-redis-development-aymenbenchaabane"
      + node_type    = "RED1-MICRO"
      + password     = (sensitive value)
      + project_id   = (known after apply)
      + tags         = [
          + "environment:development",
          + "project:calculator",
        ]
      + updated_at   = (known after apply)
      + user_name    = "admin"
      + version      = "7.2.4"

      + private_ips (known after apply)

      + public_network (known after apply)
    }

  # scaleway_redis_cluster.db["production"] will be created
  + resource "scaleway_redis_cluster" "db" {
      + certificate  = (known after apply)
      + cluster_size = 1
      + created_at   = (known after apply)
      + id           = (known after apply)
      + name         = "calculator-redis-production-aymenbenchaabane"
      + node_type    = "RED1-MICRO"
      + password     = (sensitive value)
      + project_id   = (known after apply)
      + tags         = [
          + "environment:production",
          + "project:calculator",
        ]
      + updated_at   = (known after apply)
      + user_name    = "admin"
      + version      = "7.2.4"

      + private_ips (known after apply)

      + public_network (known after apply)
    }

  # scaleway_registry_namespace.main will be created
  + resource "scaleway_registry_namespace" "main" {
      + description     = "Registre de conteneurs pour la calculatrice"
      + endpoint        = (known after apply)
      + id              = (known after apply)
      + is_public       = false
      + name            = "calculator-registry-aymenbenchaabane"
      + organization_id = (known after apply)
      + project_id      = (known after apply)
    }

Plan: 11 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + cluster_id        = (known after apply)
  + cluster_name      = "calculator-cluster-aymenbenchaabane"
  + dns_records       = {
      + development = "calculatrice-dev-aymenbenchaabane.polytech-dijon.kiowy.net"
      + production  = "calculatrice-aymenbenchaabane.polytech-dijon.kiowy.net"
    }
  + loadbalancer_ips  = {
      + development = (known after apply)
      + production  = (known after apply)
    }
  + redis_endpoints   = (sensitive value)
  + redis_passwords   = (sensitive value)
  + registry_endpoint = (known after apply)
```

---

## 📤 Outputs

Après déploiement, les informations suivantes sont disponibles :
```bash
terraform output
```

### Outputs disponibles

| Output | Description | Sensible |
|--------|-------------|----------|
| `cluster_name` | Nom du cluster Kubernetes | Non |
| `cluster_id` | ID du cluster | Non |
| `registry_endpoint` | URL du registre de conteneurs | Non |
| `loadbalancer_ips` | IPs des LoadBalancers (prod + dev) | Non |
| `dns_records` | Noms de domaine complets | Non |
| `redis_endpoints` | Endpoints Redis (host + port) | Oui |
| `redis_passwords` | Mots de passe Redis | Oui |

### Afficher un output sensible
```bash
terraform output redis_passwords
```

---

## ⚠️ Notes importantes

### Sécurité

1. **Mots de passe Redis** : Générés aléatoirement et stockés dans le state Terraform
   - Ne jamais commiter le fichier `terraform.tfstate`
   - Ajouter à `.gitignore`

2. **Credentials Scaleway** : Utiliser des variables d'environnement
   - Jamais de clés en dur dans le code

### Coûts

⚠️ **Attention** : Ces ressources ont un coût financier sur Scaleway :

| Ressource | Type | Coût estimé/mois |
|-----------|------|------------------|
| Cluster K8s | - | Gratuit |
| Nodes (2x DEV1-M) | DEV1-M | ~€20 |
| LoadBalancer (2x) | LB-S | ~€10 |
| Redis (2x) | RED1-MICRO | ~€8 |
| Registre | - | Gratuit (limite) |

**Total estimé : ~€38/mois**

### Bonnes pratiques

1. **Toujours valider avant d'appliquer**
```bash
   terraform plan
   # Vérifier les changements
   terraform apply
```

2. **Détruire les ressources inutilisées**
```bash
   terraform destroy
```

3. **Versionner le code**
```bash
   git add foundation/
   git commit -m "Update infrastructure"
   git push
```

4. **Ne pas commiter** :
   - `terraform.tfstate`
   - `terraform.tfstate.backup`
   - `.terraform/`
   - `*.tfvars` (si contient des secrets)

---

## 📚 Ressources

### Documentation officielle

- [Terraform](https://www.terraform.io/docs)
- [Scaleway Provider](https://registry.terraform.io/providers/scaleway/scaleway/latest/docs)
- [Scaleway Cloud](https://www.scaleway.com/en/docs/)

### Commandes utiles
```bash
# Afficher la liste des ressources
terraform state list

# Afficher les détails d'une ressource
terraform state show scaleway_k8s_cluster.main

# Rafraîchir le state
terraform refresh

# Importer une ressource existante
terraform import scaleway_k8s_cluster.main <cluster-id>
```

---

## 👥 Auteur

**Aymen Benchaabane**  
Projet : Calculatrice Cloud Native  
Module : Virtualisation & Cloud Computing  
École : Polytech Dijon - ILIA

---

## 📄 Licence

Projet académique - Polytech Dijon 2025