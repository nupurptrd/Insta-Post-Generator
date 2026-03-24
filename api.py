import os
from dotenv import load_dotenv

# This command reads the .env file and injects the keys into your system's memory
load_dotenv() 

# Now os.getenv can find it
my_key = os.getenv('api_key')

if my_key:
    print(f"Key loaded: {my_key[:5]}****") # Prints only the start for safety
else:
    print("Key not found! Did you name the file '.env'?")