import socket

try:
    domain = socket.gethostbyaddr("8.8.8.8")
    print(domain[0])
except socket.herror:
    print("No domain found for this IP.")
