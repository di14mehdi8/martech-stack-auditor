from config import STACK_DEFINITION, BENCHMARKS, get_all_field_keys

print("=== MarTech Stack Tools ===")
for key, tool in STACK_DEFINITION.items():
    field_count = len(tool["fields"])
    print(f"{tool['icon']} {tool['name']}: {field_count} data points")

total = sum(len(t["fields"]) for t in STACK_DEFINITION.values())
print(f"\nTotal data points collected: {total}")
print(f"Benchmarks configured: {len(BENCHMARKS)}")
print(f"\nAll field keys: {len(get_all_field_keys())}")
print("\n✅ Config loaded successfully!")
