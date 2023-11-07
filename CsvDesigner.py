csv_file = "users.csv"
with open(csv_file, "r") as f:
    lines = f.readlines()


header = lines[0]
lines = lines[1:]


ip_dict = {}


filtered_lines = []

for line in lines:
    user_data = line.strip().split(",")
    ip_address = user_data[2]
    
    if ip_address not in ip_dict:
        ip_dict[ip_address] = True
        filtered_lines.append(line)

cleaned_csv_file = "cleanedusers.csv"
with open(cleaned_csv_file, "w") as f:
    f.write(header)
    for line in filtered_lines:
        f.write(line)
