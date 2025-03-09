variable "parent_id" {
  type        = string
  description = "The ID of the parent resource (e.g., project or folder)."
}

variable "organization_id" {
  type        = string
  description = "The ID of the organization."
}

variable "pam_bindings" {
  type = list(object({
    role       = string
    principals = list(string)
    role_type  = optional(string)
  }))
  description = "List of PAM bindings."
  default     = []
}

variable "env" {
  type = object({
    pam_bindings = list(object({
      role       = string
      principals = list(string)
      role_type  = optional(string)
    }))
  })
  description = "Environment-specific PAM bindings."
  default = {
    pam_bindings = []
  }
}
