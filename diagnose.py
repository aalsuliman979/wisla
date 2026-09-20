from db_helper import diagnose_network

print("تشخيص شبكتك:")
print("-" * 50)

results = diagnose_network()
for line in results:
    print(line)