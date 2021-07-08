import os

if os.path.isfile('.env'):
    from dotenv import load_dotenv
    load_dotenv()

SESSION_SECRET = os.environ['SESSION_SECRET']
