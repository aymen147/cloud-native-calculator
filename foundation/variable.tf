variable "project_name" {
  description = "Nom du projet"
  type        = string
  default     = "calculator"
}

variable "student_name" {
  description = "Nom de l'étudiant"
  type        = string
}

variable "environments" {
  description = "Environnements à créer"
  type        = list(string)
  default     = ["production", "development"]
}

variable "region" {
  description = "Région Scaleway"
  type        = string
  default     = "fr-par"
}

variable "zone" {
  description = "Zone Scaleway"
  type        = string
  default     = "fr-par-1"
}