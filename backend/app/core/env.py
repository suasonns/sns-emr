from dotenv import load_dotenv

# Load local overrides first, then default env
load_dotenv(".env.local")
load_dotenv()