from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-bridge-manager",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Manager service for MCP Bridge instances",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/secretiveshell/mcp-bridge-manager",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.96.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "kubernetes>=28.1.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-bridge-manager=mcp_bridge_manager.main:main",
        ],
    },
)