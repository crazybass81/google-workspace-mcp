from setuptools import setup, find_packages

setup(
    name="google-workspace-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
        "google-api-python-client>=2.100.0",
        "google-auth>=2.23.0",
        "mcp>=0.9.0",
        "aiohttp>=3.9.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "cryptography>=41.0.0",
        "cachetools>=5.3.0",
    ],
)
