import yaml

file_path = "app/compliance/cms/cms_rules.yaml"

with open(file_path, "r") as f:
    data = yaml.safe_load(f)

print("✅ YAML LOADED SUCCESSFULLY\n")

print("Rule Set:", data["rule_set"])
print("Version:", data["version"])

print("\nTest Rule:")
print(data["rules"]["eligibility_terminal_illness"]["max_prognosis_months"])
