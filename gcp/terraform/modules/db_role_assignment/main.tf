locals {
  # IAM Users Management
  global_env_users = distinct(concat(
    try(var.global_assignments.readonly, []),
    try(var.global_assignments.readwrite, []),
    try(var.global_assignments.admin, []),
    try(var.environment_assignments.readonly, []),
    try(var.environment_assignments.readwrite, []),
    try(var.environment_assignments.admin, [])
  ))

  db_users = distinct(flatten([
    for instance in var.instances : [
      for db in try(instance.databases, []) : [
        for role_type in ["readonly", "readwrite", "admin"] :
          try(db.database_role_assignment[role_type], [])
      ]
    ]
  ]))

  # Detect role conflicts
  role_conflicts = {
    for conflict in flatten([
      for instance in var.instances : [
        for db in try(instance.databases, []) : [
          for user in distinct(concat(
            try(db.database_role_assignment.readonly, []),
            try(db.database_role_assignment.readwrite, []),
            try(db.database_role_assignment.admin, [])
          )) : {
            key = "${instance.instance}-${db.db_name}-${user}"
            msg = "User ${user} has multiple roles on ${db.db_name} (${instance.instance}) - Roles: ${join(", ", compact([
              for role in ["readonly", "readwrite", "admin"] :
              role if contains(try(db.database_role_assignment[role], []), user)
            ]))}"
          } if length(compact([
            for role in ["readonly", "readwrite", "admin"] :
            role if contains(try(db.database_role_assignment[role], []), user)
          ])) > 1
        ]
      ]
    ]) : conflict.key => conflict.msg
  }

  # Role assignments with instance/database info
  role_assignments = {
    for assignment in flatten([
      for instance in var.instances : [
        for db in try(instance.databases, []) : [
          for role_type in ["readonly", "readwrite", "admin"] : [
            for user in distinct(concat(
              try(db.database_role_assignment[role_type], []),
              [for u in distinct(concat(
                try(var.global_assignments[role_type], []),
                try(var.environment_assignments[role_type], [])
              )) : u if !contains(try(db.database_role_assignment[role_type], []), u)]
            )) : {
              key      = "${instance.instance}-${db.db_name}-${role_type}-${user}"
              instance = instance.instance
              db_name  = db.db_name
              role     = role_type
              user     = user
            }
          ]
        ]
      ]
    ]) : assignment.key => assignment
  }
}

# Validate no role conflicts exist
resource "terraform_data" "validate_role_assignments" {
  input = {
    conflicts = local.role_conflicts
  }

  lifecycle {
    precondition {
      condition     = length(local.role_conflicts) == 0
      error_message = <<-EOT
        Database role conflicts detected:
        ${join("\n", [for msg in values(local.role_conflicts) : "  - ${msg}"])}

        Users cannot have multiple roles on the same database.
        Please fix these role assignments before applying.
      EOT
    }
  }
}

data "google_service_account_id_token" "invoker" {
  target_audience = var.cloud_function_url
  target_service_account = var.service_account_email
}

resource "null_resource" "role_tracker" {
  for_each = {
    for assignment in local.role_assignments :
    "${assignment.instance}-${assignment.db_name}-${assignment.user}-${assignment.role}" => assignment
  }

  depends_on = [terraform_data.validate_role_assignments]

  triggers = {
    role     = each.value.role
    user     = each.value.user
    instance = each.value.instance
  }
}

resource "google_sql_user" "iam_account_users" {
  for_each = null_resource.role_tracker

  project  = var.project_id
  name     = each.value.triggers.user
  instance = each.value.triggers.instance
  type     = "CLOUD_IAM_USER"

  lifecycle {
    replace_triggered_by = [null_resource.role_tracker[each.key].id]
  }
}

resource "null_resource" "db_role_assignments" {
  for_each = local.role_assignments

  depends_on = [google_sql_user.iam_account_users]

  triggers = {
    assignment = sha256(jsonencode(each.value))
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command = <<-EOT
      set -eo pipefail

      INSTANCE="${each.value.instance}"
      PROJECT_ID="${var.project_id}"
      REGION="${var.region}"
      FULL_INSTANCE_NAME="$PROJECT_ID:$REGION:$INSTANCE"
      GCS_URI="gs://${var.bucket_name}"
      USER_EMAIL="${each.value.user}"
      DB_NAME="${each.value.db_name}"
      ROLE_TYPE="${each.value.role}"

      PAYLOAD=$(jq -n \
        --arg instance "$FULL_INSTANCE_NAME" \
        --arg role "$ROLE_TYPE" \
        --arg db "$DB_NAME" \
        --arg user "$USER_EMAIL" \
        --arg gcs_uri "$GCS_URI" \
        '{
          instance_name: $instance,
          role: $role,
          database: $db,
          user: $user,
          gcs_uri: $gcs_uri
        }'
      )

      echo "Assigning $ROLE_TYPE role to $USER_EMAIL on $DB_NAME"
      RESPONSE=$(curl -sS -X POST "${var.cloud_function_url}" \
        -H "Authorization: Bearer ${data.google_service_account_id_token.invoker.id_token}" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD")

      echo "Response: $RESPONSE"
    EOT
  }
}
