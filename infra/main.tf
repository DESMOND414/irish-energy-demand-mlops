terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "random_string" "sfx" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_resource_group" "rg" {
  name     = "energy-demand-rg"
  location = "switzerlandnorth"
}

resource "azurerm_storage_account" "lake" {
  name                     = "energylake${random_string.sfx.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true
}

resource "azurerm_storage_container" "lake" {
  name                  = "energy-lake"
  storage_account_name  = azurerm_storage_account.lake.name
  container_access_type = "private"
}

output "storage_account" {
  value = azurerm_storage_account.lake.name
}